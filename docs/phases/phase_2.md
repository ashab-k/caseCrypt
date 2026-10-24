# Phase 2 — Document Intelligence (OCR + NLP + Timeline)

> **Status**: ⏳ Pending
> **Goal**: Upload a case PDF → auto-extract parties, dates, events, cited sections → view interactive timeline.
> **Depends on**: Phase 1 (cases + documents must exist in MongoDB)
> **Unlocks**: Phase 4 (contradiction detection needs extracted sentences)

---

## What This Phase Builds

| Area | What |
|---|---|
| **Backend** | OCR service (PyMuPDF + Tesseract + python-docx), NLP service (spaCy + GPT-4o structured extraction), extraction router, timeline router |
| **Frontend** | Case detail page with entities panel, interactive vertical timeline, D3.js knowledge graph |

---

## Backend Files

| File | Purpose |
|---|---|
| `services/ocr_service.py` | Extracts text from PDF/DOCX/JPG/PNG |
| `services/nlp_service.py` | Named entity recognition + structured extraction via GPT-4o |
| `routers/extract.py` | POST /cases/{id}/extract — triggers OCR + NLP pipeline |
| `routers/timeline.py` | GET /cases/{id}/timeline — returns sorted events |

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

---

## Timeline Builder Logic

1. Collect all extracted events from every document in a case
2. Normalise dates to ISO 8601 (`YYYY-MM-DD`)
3. Sort chronologically
4. Annotate each event with `source_document`, `document_type`, `page_number`
5. Store in MongoDB collection `timelines`

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/cases/{id}/extract` | JWT | Run OCR + NLP on all unextracted documents |
| GET | `/api/cases/{id}/timeline` | JWT | Return sorted timeline events |
| GET | `/api/cases/{id}/entities` | JWT | Return all extracted entities |

---

## MongoDB Collections (New in Phase 2)

### `extractions`
```json
{
  "_id": ObjectId,
  "document_id": "string",
  "case_id": "string",
  "raw_text": "string (full extracted text)",
  "parties": {},
  "dates": [],
  "events": [],
  "claims": [],
  "cited_provisions": [],
  "extracted_at": "datetime",
  "ocr_used": false
}
```

### `timelines`
```json
{
  "_id": ObjectId,
  "case_id": "string",
  "events": [
    {
      "date": "2024-01-15",
      "description": "FIR filed at Bangalore North Police Station",
      "type": "filing",
      "source_document": "FIR_001.pdf",
      "document_type": "fir",
      "page_number": 1
    }
  ],
  "last_updated": "datetime"
}
```

---

## Frontend Components

| Component | File | Description |
|---|---|---|
| Entities Panel | `components/extraction/EntitiesPanel.tsx` | Parties, dates, provisions as tag groups |
| Timeline View | `components/timeline/TimelineView.tsx` | Vertical timeline with expand-on-click cards |
| Knowledge Graph | `components/timeline/KnowledgeGraph.tsx` | D3.js force-directed graph of entities + relations |

---

## Deliverable / Definition of Done

- [ ] Upload a native PDF → extract text → entities stored in MongoDB
- [ ] Upload a scanned PDF image → Tesseract OCR runs → entities extracted
- [ ] Upload a DOCX → python-docx extracts text → entities extracted
- [ ] Timeline shows chronologically sorted events from multiple documents
- [ ] Each timeline event shows source document name and type
- [ ] Entities panel shows parties, cited provisions, key dates
- [ ] Knowledge graph renders in the browser

---

## Known Limitations

- GPT-4o extraction costs API tokens per document (no batching in Phase 2)
- Very poor scan quality (< 150 DPI) may yield unreliable OCR — requires human review
- Knowledge graph is static JSON, not a live graph DB (Neo4j is a future upgrade)
