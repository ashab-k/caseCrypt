"""
Build chronological timelines and entity aggregates from extractions
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from models.orm import Document, Extraction


def _loads(raw: str, default: Any) -> Any:
    try:
        return json.loads(raw) if raw else default
    except json.JSONDecodeError:
        return default


def serialize_extraction(extraction: Extraction, document: Document) -> dict[str, Any]:
    parties = _loads(extraction.parties_json, {})
    return {
        "id": extraction.id,
        "document_id": extraction.document_id,
        "case_id": extraction.case_id,
        "source_document": document.original_name,
        "parties": {
            "petitioner": parties.get("petitioner") or [],
            "respondent": parties.get("respondent") or [],
            "counsel": parties.get("counsel") or [],
        },
        "dates": _loads(extraction.dates_json, []),
        "events": _loads(extraction.events_json, []),
        "claims": _loads(extraction.claims_json, []),
        "cited_provisions": _loads(extraction.cited_provisions_json, []),
        "spacy_entities": _loads(extraction.spacy_entities_json, []),
        "extracted_at": extraction.extracted_at,
        "ocr_used": extraction.ocr_used,
        "extraction_method": extraction.extraction_method,
        "text_preview": (extraction.raw_text or "")[:400],
    }


def build_timeline(
    pairs: list[tuple[Extraction, Document]],
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    last_updated: datetime | None = None

    for extraction, document in pairs:
        if last_updated is None or extraction.extracted_at > last_updated:
            last_updated = extraction.extracted_at
        for ev in _loads(extraction.events_json, []):
            events.append(
                {
                    "date": ev.get("date"),
                    "description": ev.get("description") or "",
                    "type": ev.get("type") or "other",
                    "source_document": document.original_name,
                    "document_id": document.id,
                    "document_type": document.file_type,
                    "page_number": ev.get("page_number"),
                }
            )
        # Promote dated mentions into timeline when events are sparse
        for d in _loads(extraction.dates_json, []):
            if not d.get("date"):
                continue
            events.append(
                {
                    "date": d.get("date"),
                    "description": d.get("event") or f"Date mentioned: {d.get('date')}",
                    "type": "other",
                    "source_document": document.original_name,
                    "document_id": document.id,
                    "document_type": document.file_type,
                    "page_number": None,
                }
            )

    def sort_key(item: dict[str, Any]):
        date = item.get("date") or ""
        return (date == "" or date is None, date or "", item.get("description") or "")

    # Deduplicate near-identical timeline rows
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ev in sorted(events, key=sort_key):
        key = f"{ev.get('date')}|{ev.get('description', '')[:100]}|{ev.get('source_document')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ev)

    return {
        "events": deduped,
        "last_updated": last_updated,
    }


def aggregate_entities(pairs: list[tuple[Extraction, Document]]) -> dict[str, Any]:
    parties = {"petitioner": [], "respondent": [], "counsel": []}
    dates: list[dict[str, str]] = []
    claims: list[str] = []
    cited: list[dict[str, str]] = []
    spacy_entities: list[dict[str, str]] = []

    def extend_unique(target: list, values: list):
        for v in values:
            if v and v not in target:
                target.append(v)

    for extraction, _document in pairs:
        p = _loads(extraction.parties_json, {})
        extend_unique(parties["petitioner"], p.get("petitioner") or [])
        extend_unique(parties["respondent"], p.get("respondent") or [])
        extend_unique(parties["counsel"], p.get("counsel") or [])
        for d in _loads(extraction.dates_json, []):
            if d not in dates:
                dates.append(d)
        extend_unique(claims, _loads(extraction.claims_json, []))
        for c in _loads(extraction.cited_provisions_json, []):
            if c not in cited:
                cited.append(c)
        for e in _loads(extraction.spacy_entities_json, []):
            if e not in spacy_entities:
                spacy_entities.append(e)

    return {
        "parties": parties,
        "dates": dates,
        "claims": claims,
        "cited_provisions": cited,
        "spacy_entities": spacy_entities,
        "document_count_extracted": len(pairs),
    }


def build_knowledge_graph(pairs: list[tuple[Extraction, Document]], case_id: str) -> dict[str, Any]:
    nodes: dict[str, dict[str, str]] = {}
    links: list[dict[str, str]] = []

    case_node_id = f"case:{case_id}"
    nodes[case_node_id] = {"id": case_node_id, "label": "Case", "group": "case"}

    def add_node(node_id: str, label: str, group: str):
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": label[:60], "group": group}

    entities = aggregate_entities(pairs)
    for role, names in entities["parties"].items():
        for name in names:
            nid = f"party:{role}:{name.lower()}"
            add_node(nid, name, "party")
            links.append({"source": case_node_id, "target": nid, "label": role})

    for prov in entities["cited_provisions"]:
        label = f"{prov.get('act', '')} {prov.get('section', '')}".strip()
        nid = f"law:{label.lower()}"
        add_node(nid, label or "Provision", "law")
        links.append({"source": case_node_id, "target": nid, "label": "cites"})

    for extraction, document in pairs:
        doc_id = f"doc:{document.id}"
        add_node(doc_id, document.original_name, "document")
        links.append({"source": case_node_id, "target": doc_id, "label": "contains"})
        for ev in _loads(extraction.events_json, [])[:12]:
            desc = (ev.get("description") or "")[:48]
            if not desc:
                continue
            eid = f"event:{document.id}:{desc.lower()}"
            add_node(eid, desc, "event")
            links.append({"source": doc_id, "target": eid, "label": ev.get("type") or "event"})

    return {
        "case_id": case_id,
        "nodes": list(nodes.values()),
        "links": links,
    }
