# Phase 2 — Document Intelligence (OCR + NLP + Timeline)

> **Status**: ✅ Complete
> **Goal**: Upload a case PDF → auto-extract parties, dates, events, cited sections → view interactive timeline.
> **Depends on**: Phase 1 (cases + documents must exist in SQLite)
> **Unlocks**: Phase 4 (contradiction detection needs extracted sentences)

---

## What This Phase Builds

| Area | What |
|---|---|
| **Backend** | OCR service (PyMuPDF + Tesseract + python-docx), NLP service (spaCy + GPT-4o structured extraction), extraction router, timeline / entities / knowledge-graph endpoints |
| **Frontend** | Case detail page with entities panel, interactive vertical timeline, D3.js knowledge graph, Run extraction CTA |

---

## Backend Files

| File | Purpose |
|---|---|
| `services/ocr_service.py` | Extracts text from PDF/DOCX/JPG/PNG |
| `services/nlp_service.py` | Named entity recognition + structured extraction via GPT-4o (heuristic fallback) |
| `services/timeline_service.py` | Timeline build, entity aggregate, knowledge graph |
| `routers/extract.py` | Extract / timeline / entities / knowledge-graph endpoints |
| `models/extraction.py` | Pydantic schemas for Phase 2 responses |

---

## OCR Service Logic

```
Input: file path (pdf / docx / jpg / png)
       ↓
Is PDF?
  → Has text layer? → PyMuPDF (pymupdf4llm.to_markdown)
  → Scanned?        → PyMuPDF render page → Tesseract OCR
Is DOCX?            → python-docx
Is Image?           → Tesseract OCR directly

Output: List[{ page_number, text, is_ocr: bool }]
```

**Key library**: `pymupdf4llm.to_markdown()` — returns Markdown-formatted text preserving headings, lists and tables for better RAG chunking later.

---

## NLP Extraction Pipeline

### Stage 1 — spaCy EntityRuler (deterministic, fast)
Custom legal patterns added to `en_core_web_sm`:
```python
patterns = [
    {"label": "CASE_CITATION",  "pattern": [{"TEXT": {"REGEX": r"\d{4}\s\(\d+\)\s[A-Z]+"}}]},
    {"label": "SECTION_REF",    "pattern": [{"LOWER": "section"}, {"TEXT": {"REGEX": r"\d+[A-Za-z]?"}}]},
    {"label": "IPC_SECTION",    "pattern": [{"TEXT": {"REGEX": r"S\.\s?\d+"}}, {"LOWER": "ipc"}]},
    {"label": "FIR_NUMBER",     "pattern": [{"LOWER": "fir"}, {"LOWER": "no"}, {"TEXT": {"REGEX": r"\d+"}}]},
    {"label": "COURT",          "pattern": [{"LOWER": {"IN": ["high", "supreme", "district"]}}, {"LOWER": "court"}]},
]
```

### Stage 2 — GPT-4o Structured Extraction
Prompt asks for JSON output:
```json
{
  "parties": {
    "petitioner": ["name", ...],
    "respondent": ["name", ...],
    "counsel": ["name", ...]
  },
  "dates": [{"date": "YYYY-MM-DD", "event": "description"}],
  "events": [{"date": "...", "description": "...", "type": "filing|hearing|judgment|incident"}],
  "claims": ["claim text", ...],
  "cited_provisions": [{"act": "IPC", "section": "302", "description": "..."}]
}
```

When `OPENAI_API_KEY` is unset, heuristic extraction still populates parties / dates / events / provisions.

---

## Timeline Builder Logic

1. Collect all extracted events from every document in a case
2. Normalise dates to ISO 8601 (`YYYY-MM-DD`)
3. Sort chronologically
4. Annotate each event with `source_document`, `document_type`, `page_number`
5. Serve via `GET /api/cases/{id}/timeline` (built from `extractions` table)

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/cases/{id}/extract` | JWT | Run OCR + NLP on unextracted documents (`?force=true` to re-run) |
| GET | `/api/cases/{id}/timeline` | JWT | Return sorted timeline events |
| GET | `/api/cases/{id}/entities` | JWT | Return all extracted entities |
| GET | `/api/cases/{id}/knowledge-graph` | JWT | Return nodes/links for D3 graph |

---

## SQLite Tables (Phase 2)

### `extractions`
Stores per-document OCR text + structured NLP JSON fields (`parties_json`, `dates_json`, `events_json`, `claims_json`, `cited_provisions_json`, `spacy_entities_json`).

`documents.extracted` flags whether a file has been processed.

---

## Frontend Components

| Component | File | Description |
|---|---|---|
| Entities Panel | `components/extraction/EntitiesPanel.tsx` | Parties, dates, provisions as tag groups |
| Timeline View | `components/timeline/TimelineView.tsx` | Vertical timeline with expand-on-click cards |
| Knowledge Graph | `components/timeline/KnowledgeGraph.tsx` | D3.js force-directed graph of entities + relations |

---

## Deliverable / Definition of Done

- [x] Upload a native PDF → extract text → entities stored in SQLite
- [x] Upload a scanned PDF image → Tesseract OCR runs → entities extracted
- [x] Upload a DOCX → python-docx extracts text → entities extracted
- [x] Timeline shows chronologically sorted events from multiple documents
- [x] Each timeline event shows source document name and type
- [x] Entities panel shows parties, cited provisions, key dates
- [x] Knowledge graph renders in the browser

---

## Known Limitations

- GPT-4o extraction costs API tokens per document (no batching in Phase 2)
- Very poor scan quality (< 150 DPI) may yield unreliable OCR — requires human review
- Knowledge graph is static JSON, not a live graph DB (Neo4j is a future upgrade)
- Without `OPENAI_API_KEY`, extraction uses heuristics (still useful for demos)
