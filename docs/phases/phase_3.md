# Phase 3 — Legal RAG Research Engine

> **Status**: ⏳ Pending
> **Goal**: Ask any legal question → get a cited answer grounded in Indian statutes (IPC, CrPC, Constitution, Evidence Act, IT Act).
> **Depends on**: Phase 1 (auth + cases); Phase 2 not strictly required (corpus is global, not per-case)
> **Unlocks**: Phase 4 (contradiction detection can cross-reference statute conflicts)

---

## What This Phase Builds

| Area | What |
|---|---|
| **Backend** | `seed.py` — downloads + chunks + embeds Indian legal corpus into ChromaDB; LangChain LCEL RAG chain with GPT-4o; `/api/query` endpoint |
| **Frontend** | Legal Research page — search bar + chat-style answer panel with expandable source citations |

---

## Backend Files

| File | Purpose |
|---|---|
| `seed.py` | One-time corpus seeding script (CLI: `python seed.py`) |
| `services/rag_service.py` | ChromaDB retriever + LangChain chain + GPT-4o generation |
| `routers/rag.py` | POST /api/query, POST /api/search |

---

## Indian Legal Corpus

### Acts to Seed
| Act | Sections / Articles | Source URL |
|---|---|---|
| Indian Penal Code, 1860 (IPC) | 511 sections | `https://www.indiacode.nic.in/handle/123456789/2263` |
| Code of Criminal Procedure, 1973 (CrPC) | 484 sections | `https://www.indiacode.nic.in/handle/123456789/1593` |
| Constitution of India | 448 articles + schedules | `https://www.indiacode.nic.in/handle/123456789/1370` |
| Indian Evidence Act, 1872 | 167 sections | `https://www.indiacode.nic.in/handle/123456789/2190` |
| Information Technology Act, 2000 | 94 sections | `https://www.indiacode.nic.in/handle/123456789/1999` |

### Chunking Strategy
```python
RecursiveCharacterTextSplitter(
    chunk_size=800,       # ~200 words — enough for 1-2 sections
    chunk_overlap=150,    # Preserve context across section boundaries
    separators=["\n\n", "\n", ".", " "]
)
```

### Chunk Metadata (stored in ChromaDB per chunk)
```python
{
    "act": "IPC",
    "section": "302",
    "title": "Punishment for murder",
    "source_url": "https://indiacode.nic.in/...",
    "chunk_index": 0
}
```

---

## Seeding Script (`seed.py`)

```
Flow:
1. Check if ChromaDB collection "indian_legal_corpus" already has documents
   → If yes AND --force not passed → skip (already seeded)
2. For each act:
   a. Download HTML from IndiaCode.gov.in
   b. Parse with BeautifulSoup → extract section text + section numbers
   c. Split with RecursiveCharacterTextSplitter
   d. Embed with all-MiniLM-L6-v2 (local, CPU)
   e. Store in ChromaDB with metadata
3. Print summary: X chunks embedded for Y acts
```

CLI usage:
```bash
python seed.py           # Skip if already seeded
python seed.py --force   # Re-seed even if collection exists
```

---

## RAG Chain Architecture (LangChain LCEL)

```
User Question
     ↓
MultiQueryRetriever
  → Generates 3 legal rephrasing of the question
  → Each queries ChromaDB (semantic) + BM25 (lexical)
  → Results merged + deduplicated
     ↓
ContextualCompressionRetriever
  → Strips boilerplate from retrieved chunks
  → Keeps only sentences relevant to the question
     ↓
Cross-encoder re-ranking (all-MiniLM-L6-v2)
  → Re-ranks top-k chunks by relevance score
     ↓
GPT-4o (gpt-4o, temperature=0)
  → Strict prompt: "Answer ONLY from the provided context.
     If the answer is not in the context, say so."
  → Returns: answer + list of source chunks used
     ↓
Response:
  {
    "answer": "Section 302 IPC prescribes...",
    "sources": [
      { "act": "IPC", "section": "302", "text": "...", "url": "..." }
    ],
    "confidence": "high"
  }
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/query` | JWT | Full RAG chain — question → cited answer |
| POST | `/api/search` | JWT | Semantic search only — return top-k passages |
| GET | `/api/corpus/status` | JWT | Check if corpus is seeded + chunk count |

### Request / Response

**POST `/api/query`**
```json
// Request
{ "question": "What is the punishment for murder under IPC?" }

// Response
{
  "answer": "Section 302 of the Indian Penal Code prescribes death, or imprisonment for life, and shall also be liable to fine.",
  "sources": [
    {
      "act": "IPC",
      "section": "302",
      "title": "Punishment for murder",
      "text": "Whoever commits murder shall be punished with death, or imprisonment for life...",
      "url": "https://indiacode.nic.in/..."
    }
  ],
  "confidence": "high",
  "retrieved_chunks": 5
}
```

---

## ChromaDB Collection

- **Collection name**: `indian_legal_corpus`
- **Embedding function**: `sentence-transformers/all-MiniLM-L6-v2` (local)
- **Distance metric**: Cosine
- **Persist directory**: `backend/data/chroma_db/`

> ⚠️ This collection is **global** — shared across all users and cases. It contains only public statute text, no user data.

---

## Frontend: Legal Research Page

**Route**: `/research`

| Component | Description |
|---|---|
| Search bar | Natural language question input with submit |
| Answer card | Formatted answer text with act/section badge |
| Sources accordion | Expandable list of source statute passages |
| Confidence badge | HIGH / MEDIUM / LOW based on retrieval score |
| Search history | Last 10 queries for the session |

---

## Deliverable / Definition of Done

- [ ] `seed.py` runs and populates ChromaDB without errors
- [ ] Second run of `seed.py` skips re-seeding (idempotent)
- [ ] `python seed.py --force` re-seeds from scratch
- [ ] POST `/api/query` returns a cited answer for "What is Section 302 IPC?"
- [ ] Source text in response matches the actual IPC section text
- [ ] Frontend research page shows answer with expandable sources
- [ ] Corpus status endpoint confirms total chunk count per act

---

## Known Limitations

- Corpus is a static snapshot; amendments after seeding are not reflected
- `all-MiniLM-L6-v2` is a general-purpose model, not legally fine-tuned — may miss subtle legal terminology matches
- IndiaCode.gov.in HTML structure may change; parser will need updating if it does
- Very long questions may exceed GPT-4o context window with many retrieved chunks — mitigated by ContextualCompression
