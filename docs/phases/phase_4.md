# Phase 4 — Contradiction Detection & Case Similarity

> **Status**: ⏳ Pending
> **Goal**: Detect cross-document factual, temporal, and testimonial contradictions across case files + compute hybrid case similarity against precedent benchmarks.
> **Depends on**: Phase 1 (cases + documents in MongoDB), Phase 2 (OCR + NLP extractions with sentence boundaries and dates)
> **Unlocks**: Phase 5 (immutable audit logging of verified contradiction reports) and unified lawyer dashboard

---

## What This Phase Builds

| Area | What |
|---|---|
| **Backend** | 3-stage contradiction detection pipeline (Semantic filter → DeBERTa NLI → GPT-4o verifier), hybrid BM25 + dense case similarity engine, case-level grounded Q&A router |
| **Frontend** | Contradiction review panel (side-by-side statement diffs, conflict badges, lawyer action buttons), case similarity visualizer with statute alignment, case chat drawer |

---

## Backend Files

| File | Purpose |
|---|---|
| `services/contradiction_service.py` | 3-stage contradiction pipeline (candidate pairing, NLI scoring, GPT-4o verification) |
| `services/similarity_service.py` | Hybrid BM25 (40%) + semantic cosine (60%) similarity matching across cases |
| `services/case_qa_service.py` | Case-specific RAG over extracted case documents, timeline, and entities |
| `routers/contradictions.py` | POST /cases/{id}/contradictions/detect, GET /cases/{id}/contradictions, PATCH /cases/{id}/contradictions/{flag_id} |
| `routers/similarity.py` | POST /cases/{id}/similarity, GET /cases/{id}/similarity |
| `routers/case_qa.py` | POST /cases/{id}/chat — natural language Q&A grounded in active case docs |

---

## Contradiction Detection Pipeline (3-Stage)

Cross-document contradiction detection prevents lawyers from missing conflicting claims across large case bundles (e.g., FIR vs. Bail Application vs. Witness Deposition).

```
Extracted Sentences & Claims from All Documents in Case
                         ↓
[Stage 1: Semantic Candidate Pairing]
  - sentence-transformers (all-MiniLM-L6-v2)
  - Filters out un-related sentence pairs (keeps pairs with cosine similarity > 0.60)
  - Enforces cross-document rule: Doc_A != Doc_B
                         ↓
[Stage 2: Cross-Encoder NLI Classification]
  - Model: cross-encoder/nli-deberta-v3-small (local, fast inference)
  - Classifies pair: [Entailment, Neutral, Contradiction]
  - Retains pairs where Contradiction probability > 0.70
                         ↓
[Stage 3: LLM Reasoning & Legal Validation]
  - GPT-4o (temperature=0) with structured output
  - Filters false alarms (context shifts, different speakers)
  - Categorizes contradiction type: Temporal/Alibi, Factual, Numerical/Financial, Testimonial
  - Generates clear legal explanation for lawyer review
                         ↓
Output: Flagged contradiction record in MongoDB with review status "pending"
```

### Contradiction Types Identified
1. **Temporal / Alibi**: Accused claimed to be in City A on date X, but witness/FIR records them in City B.
2. **Factual**: Conflicting descriptions of incident location, weapon, or presence of individuals.
3. **Numerical / Financial**: Discrepancies in amounts claimed, cheques dishonored, or recovery figures.
4. **Testimonial**: Divergent witness statements between preliminary deposition and cross-examination.

---

## Case Similarity Engine (Hybrid)

Computes multi-dimensional similarity between the active case and repository/benchmark cases:

```
Combined Similarity = (0.40 × BM25_Lexical) + (0.60 × Cosine_Semantic)
```

- **Lexical (BM25)**: Evaluates exact overlap of legal keywords, statute sections (e.g., `Section 302 IPC`, `Section 138 NI Act`), court names, and specific claim terms.
- **Semantic (Cosine)**: Encodes synthesized case summary and core facts using `all-MiniLM-L6-v2`.
- **Weighted Features**:
  - Cited statutory provisions: 1.5× weight
  - Extracted core facts & timeline events: 1.2× weight
  - General case background text: 1.0× weight

---

## Case Natural Language Q&A Engine

Allows counsel to interrogate the active case bundle in natural language:
- Retrieves relevant excerpts from case documents, timeline events, and entity records.
- Injects full provenance into prompt context.
- Output includes answer text plus explicit document name, page number, and source quote.

---

## API Endpoints

### Contradictions
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/cases/{id}/contradictions/detect` | JWT | Triggers full contradiction scan across case documents |
| GET | `/api/cases/{id}/contradictions` | JWT | List flagged contradictions (filter by status: `pending`, `reviewed`, `dismissed`) |
| PATCH | `/api/cases/{id}/contradictions/{flag_id}` | JWT | Update review state (`status: "reviewed" \| "dismissed"`, optional `lawyer_notes`) |

### Similarity
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/cases/{id}/similarity` | JWT | Compute similarity against reference cases |
| GET | `/api/cases/{id}/similarity` | JWT | Retrieve cached similarity matches and statute overlaps |

### Case Q&A
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/cases/{id}/chat` | JWT | Query case facts with citation-grounded response |

---

## Request & Response Examples

### POST `/api/cases/{id}/contradictions/detect`
```json
// Response
{
  "case_id": "671ad48f12c980...",
  "status": "completed",
  "contradictions_found": 2,
  "pairs_evaluated": 148,
  "scan_duration_ms": 1420
}
```

### GET `/api/cases/{id}/contradictions`
```json
// Response
[
  {
    "id": "671b2390a1f9e8...",
    "case_id": "671ad48f12c980...",
    "type": "temporal",
    "confidence": "high",
    "nli_score": 0.88,
    "statement_a": {
      "document_id": "doc_001",
      "document_name": "FIR_Complaint.pdf",
      "page": 2,
      "text": "Accused was present at the site of the altercation in Indiranagar at 8:30 PM on 12-01-2024."
    },
    "statement_b": {
      "document_id": "doc_004",
      "document_name": "Bail_Application.docx",
      "page": 4,
      "text": "The applicant was attending a corporate conference in Hyderabad from 10-01-2024 to 14-01-2024."
    },
    "explanation": "Direct temporal conflict regarding accused location on the evening of 12-01-2024.",
    "status": "pending",
    "lawyer_notes": null,
    "created_at": "2026-10-24T22:30:00Z"
  }
]
```

---

## MongoDB Collections (New in Phase 4)

### `contradictions`
```json
{
  "_id": ObjectId,
  "case_id": "string",
  "type": "temporal | factual | numerical | testimonial",
  "confidence": "high | medium | low",
  "nli_score": 0.88,
  "statement_a": {
    "document_id": "string",
    "document_name": "string",
    "page": 2,
    "text": "string"
  },
  "statement_b": {
    "document_id": "string",
    "document_name": "string",
    "page": 4,
    "text": "string"
  },
  "explanation": "string",
  "status": "pending | reviewed | dismissed",
  "lawyer_notes": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `case_similarities`
```json
{
  "_id": ObjectId,
  "case_id": "string",
  "matches": [
    {
      "benchmark_case_id": "string",
      "case_title": "string",
      "combined_score": 0.82,
      "lexical_score": 0.78,
      "semantic_score": 0.85,
      "shared_sections": ["IPC 302", "IPC 34"],
      "summary_overlap": "string"
    }
  ],
  "computed_at": "datetime"
}
```

---

## Frontend Components

| Component | File | Description |
|---|---|---|
| Contradiction Panel | `components/contradiction/ContradictionPanel.tsx` | Overview badge count, filter tabs (`pending`, `reviewed`, `dismissed`) |
| Contradiction Card | `components/contradiction/ContradictionCard.tsx` | Side-by-side statement view with document badges, source quote, and action buttons |
| Similarity Visualizer | `components/similarity/CaseSimilarityView.tsx` | Ranked precedent matches, score breakdown, and shared statute chips |
| Case Chat Drawer | `components/chat/CaseChatDrawer.tsx` | Interactive conversation panel with clickable inline citations |

---

## Deliverable / Definition of Done

- [ ] Contradiction scanner processes extracted text across multiple documents in a case
- [ ] Cross-encoder NLI model filters pairs with high contradiction probability (> 0.70)
- [ ] GPT-4o verification step discards trivial false alarms and categorizes genuine conflicts
- [ ] Lawyer can mark contradiction flags as `reviewed` or `dismissed` with custom notes
- [ ] Hybrid similarity endpoint calculates combined lexical (BM25) and semantic score
- [ ] Case Chat returns accurate answers citing source document name and page number
- [ ] Frontend displays side-by-side comparison cards with responsive status controls

---

## Known Limitations

- Running NLI across all sentence pairs scales quadratically $O(N^2)$; stage 1 semantic filtering is strictly necessary to keep runtimes under 10 seconds.
- Sarcasm, figurative language, or rhetorical legal arguments may occasionally trigger false positives.
- Cross-examination transcripts with contradictory testimony by design require lawyer discretion to evaluate credibility rather than automated labeling.
