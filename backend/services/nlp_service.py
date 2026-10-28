"""
NLP extraction — spaCy EntityRuler + GPT-4o (with heuristic fallback)
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from config import settings

LEGAL_PATTERNS = [
    {
        "label": "CASE_CITATION",
        "pattern": [{"TEXT": {"REGEX": r"\d{4}"}}, {"TEXT": {"REGEX": r"\(\d+\)"}}, {"IS_UPPER": True}],
    },
    {
        "label": "SECTION_REF",
        "pattern": [{"LOWER": "section"}, {"TEXT": {"REGEX": r"\d+[A-Za-z]?"}}],
    },
    {
        "label": "IPC_SECTION",
        "pattern": [
            {"TEXT": {"REGEX": r"(?i)s(?:ection)?\.?"}},
            {"TEXT": {"REGEX": r"\d+[A-Za-z]?"}},
            {"LOWER": "ipc"},
        ],
    },
    {
        "label": "FIR_NUMBER",
        "pattern": [
            {"LOWER": "fir"},
            {"LOWER": {"IN": ["no", "no.", "number", "#"]}},
            {"TEXT": {"REGEX": r"\d+"}},
        ],
    },
    {
        "label": "COURT",
        "pattern": [
            {"LOWER": {"IN": ["high", "supreme", "district", "sessions"]}},
            {"LOWER": "court"},
        ],
    },
]


@lru_cache(maxsize=1)
def _get_nlp():
    import spacy
    from spacy.pipeline import EntityRuler

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        nlp = spacy.blank("en")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")

    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner" if "ner" in nlp.pipe_names else None)
    else:
        ruler = nlp.get_pipe("entity_ruler")

    if isinstance(ruler, EntityRuler) or hasattr(ruler, "add_patterns"):
        ruler.add_patterns(LEGAL_PATTERNS)  # type: ignore[attr-defined]
    return nlp


def run_spacy(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    nlp = _get_nlp()
    # Cap very long docs for latency
    doc = nlp(text[:100_000])
    seen: set[tuple[str, str]] = set()
    entities: list[dict[str, str]] = []
    for ent in doc.ents:
        key = (ent.label_, ent.text.strip())
        if not key[1] or key in seen:
            continue
        seen.add(key)
        entities.append({"label": ent.label_, "text": key[1]})
    return entities


def extract_structured(text: str, spacy_entities: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """
    Prefer GPT-4o when OPENAI_API_KEY is set; otherwise heuristic extraction.
    """
    spacy_entities = spacy_entities if spacy_entities is not None else run_spacy(text)
    if settings.openai_api_key:
        try:
            result = _extract_with_openai(text)
            result["extraction_method"] = "openai"
            result["spacy_entities"] = spacy_entities
            return result
        except Exception:
            # Fall through to heuristic if API fails
            pass

    result = _extract_heuristic(text, spacy_entities)
    result["extraction_method"] = "heuristic"
    result["spacy_entities"] = spacy_entities
    return result


def _extract_with_openai(text: str) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    clipped = text[:24_000]
    system = (
        "You are a legal document analyst for Indian law. "
        "Extract structured facts only from the provided text. "
        "Return valid JSON only, no markdown."
    )
    user = f"""Extract from this legal document text:

{clipped}

Return JSON with this exact shape:
{{
  "parties": {{"petitioner": [], "respondent": [], "counsel": []}},
  "dates": [{{"date": "YYYY-MM-DD", "event": "description"}}],
  "events": [{{"date": "YYYY-MM-DD or null", "description": "...", "type": "filing|hearing|judgment|incident|other", "page_number": null}}],
  "claims": ["..."],
  "cited_provisions": [{{"act": "IPC", "section": "302", "description": "..."}}]
}}
Use ISO dates when possible. If unknown, use null or empty lists."""

    response = client.chat.completions.create(
        model=settings.llm_model or "gpt-4o",
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    return _normalize_payload(data)


def _extract_heuristic(text: str, spacy_entities: list[dict[str, str]]) -> dict[str, Any]:
    parties = {"petitioner": [], "respondent": [], "counsel": []}
    lower = text.lower()

    # vs / versus split
    vs_match = re.search(
        r"([A-Z][A-Za-z .,'-]{2,60})\s+(?:v(?:ersus)?\.?|vs\.?)\s+([A-Z][A-Za-z .,'-]{2,60})",
        text,
    )
    if vs_match:
        parties["petitioner"].append(vs_match.group(1).strip(" ,.-"))
        parties["respondent"].append(vs_match.group(2).strip(" ,.-"))

    for label, key in (
        ("petitioner", "petitioner"),
        ("respondent", "respondent"),
        ("accused", "respondent"),
        ("complainant", "petitioner"),
        ("counsel", "counsel"),
        ("advocate", "counsel"),
    ):
        for m in re.finditer(
            rf"{label}\s*[:\-]\s*([A-Z][A-Za-z .,'-]{{2,60}})",
            text,
            flags=re.IGNORECASE,
        ):
            name = m.group(1).strip(" ,.-")
            if name and name not in parties[key]:
                parties[key].append(name)

    dates: list[dict[str, str]] = []
    date_patterns = [
        (r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", "%d/%m/%Y"),
        (r"\b(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
        (
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
            "%d %B %Y",
        ),
    ]
    seen_dates: set[str] = set()
    for pattern, _fmt in date_patterns:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            raw = m.group(1)
            iso = _normalize_date(raw)
            if iso and iso not in seen_dates:
                seen_dates.add(iso)
                ctx_start = max(0, m.start() - 40)
                ctx_end = min(len(text), m.end() + 60)
                snippet = re.sub(r"\s+", " ", text[ctx_start:ctx_end]).strip()
                dates.append({"date": iso, "event": snippet})

    events: list[dict[str, Any]] = []
    event_keywords = {
        "filing": [r"\bfir\b", r"\bfiled\b", r"\bcomplaint\b", r"\bpetition\b"],
        "hearing": [r"\bhearing\b", r"\blisted\b", r"\badjourn"],
        "judgment": [r"\bjudgment\b", r"\bordered\b", r"\bdisposed\b", r"\bconviction\b"],
        "incident": [r"\bincident\b", r"\boccurred\b", r"\ballegedly\b"],
    }
    for etype, patterns in event_keywords.items():
        for pat in patterns:
            for m in re.finditer(pat, lower):
                start = max(0, m.start() - 50)
                end = min(len(text), m.end() + 120)
                snippet = re.sub(r"\s+", " ", text[start:end]).strip()
                nearby_date = None
                for d in dates:
                    if d["date"] and d["date"] in snippet:
                        nearby_date = d["date"]
                        break
                if not nearby_date and dates:
                    # attach first date near keyword window if any date string nearby
                    window = text[start:end]
                    for d in dates:
                        if d.get("event") and d["event"][:20] in window:
                            nearby_date = d["date"]
                            break
                events.append(
                    {
                        "date": nearby_date,
                        "description": snippet[:240],
                        "type": etype,
                        "page_number": None,
                    }
                )
                if len(events) >= 25:
                    break
            if len(events) >= 25:
                break

    # Deduplicate events by description prefix
    deduped: list[dict[str, Any]] = []
    seen_desc: set[str] = set()
    for ev in events:
        key = ev["description"][:80].lower()
        if key in seen_desc:
            continue
        seen_desc.add(key)
        deduped.append(ev)

    cited: list[dict[str, str]] = []
    for ent in spacy_entities:
        if ent["label"] in {"SECTION_REF", "IPC_SECTION"}:
            section = re.search(r"\d+[A-Za-z]?", ent["text"])
            cited.append(
                {
                    "act": "IPC" if "ipc" in ent["text"].lower() else "Unknown",
                    "section": section.group(0) if section else ent["text"],
                    "description": ent["text"],
                }
            )
    for m in re.finditer(
        r"(?:section|s\.?)\s*(\d+[A-Za-z]?)\s*(?:of\s+the\s+)?(ipc|crpc|evidence act|it act)?",
        text,
        flags=re.IGNORECASE,
    ):
        act = (m.group(2) or "Unknown").upper().replace("EVIDENCE ACT", "Evidence Act")
        if act == "CRPC":
            act = "CrPC"
        entry = {"act": act if act != "UNKNOWN" else "Unknown", "section": m.group(1), "description": m.group(0)}
        if entry not in cited:
            cited.append(entry)

    claims: list[str] = []
    for m in re.finditer(
        r"(?:prays?|claims?|alleges?|submits?)\s+(?:that\s+)?(.{20,160})",
        text,
        flags=re.IGNORECASE,
    ):
        claim = re.sub(r"\s+", " ", m.group(0)).strip()
        if claim not in claims:
            claims.append(claim[:200])
        if len(claims) >= 10:
            break

    return {
        "parties": parties,
        "dates": dates[:40],
        "events": deduped[:40],
        "claims": claims,
        "cited_provisions": cited[:40],
    }


_ALLOWED_EVENT_TYPES = {"filing", "hearing", "judgment", "incident", "other"}


def _normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
    parties = data.get("parties") or {}
    events: list[dict[str, Any]] = []
    for ev in data.get("events") or []:
        if not isinstance(ev, dict):
            continue
        etype = str(ev.get("type") or "other").lower().strip()
        if etype not in _ALLOWED_EVENT_TYPES:
            etype = "other"
        events.append(
            {
                "date": ev.get("date"),
                "description": str(ev.get("description") or "").strip(),
                "type": etype,
                "page_number": ev.get("page_number"),
            }
        )
    dates: list[dict[str, str]] = []
    for d in data.get("dates") or []:
        if not isinstance(d, dict) or not d.get("date"):
            continue
        dates.append(
            {
                "date": str(d["date"]),
                "event": str(d.get("event") or ""),
            }
        )

    claims = [str(c) for c in (data.get("claims") or []) if c]
    cited: list[dict[str, str]] = []
    for c in data.get("cited_provisions") or []:
        if not isinstance(c, dict):
            continue
        cited.append(
            {
                "act": str(c.get("act") or "Unknown"),
                "section": str(c.get("section") or ""),
                "description": str(c.get("description") or ""),
            }
        )

    return {
        "parties": {
            "petitioner": list(parties.get("petitioner") or []),
            "respondent": list(parties.get("respondent") or []),
            "counsel": list(parties.get("counsel") or []),
        },
        "dates": dates,
        "events": [e for e in events if e["description"]],
        "claims": claims,
        "cited_provisions": [c for c in cited if c["section"]],
    }


def _normalize_date(raw: str) -> str | None:
    from datetime import datetime

    raw = raw.strip()
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d %B %Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw if re.match(r"^\d{4}-\d{2}-\d{2}$", raw) else None
