# CaseCrypt — Global Project Context

> **Last updated**: Phase 1 (Foundation & Auth) — In Progress
> Read this file before touching any part of the codebase.

---

## What Is CaseCrypt?

CaseCrypt is a **Smart Legal Case Intelligence System** — a full-stack web application for Indian legal professionals that combines:
- **AI/NLP** for document understanding, timeline construction, legal research and contradiction detection
- **Blockchain-based evidence integrity** via SHA-256 hashing on an immutable ledger

It is a **decision-support tool**, not an autonomous legal advisor. Every AI output is grounded in citations and presented for lawyer review.

---

## Repository Structure

```
caseCrypt/
├── docs/                        ← YOU ARE HERE — all context lives here
│   ├── REQUIREMENTS.md          ← Full functional + non-functional requirements
│   ├── GLOBAL_CONTEXT.md        ← This file
│   ├── phases/
│   │   ├── phase_1.md           ← Auth, Cases, Upload
│   │   ├── phase_2.md           ← OCR, NLP, Timeline
│   │   ├── phase_3.md           ← Legal RAG + Indian Corpus
│   │   ├── phase_4.md           ← Contradiction Detection
│   │   └── phase_5.md           ← Blockchain Evidence Integrity
│   └── components/
│       ├── auth.md              ← Auth service context
│       ├── cases.md             ← Case management context
│       ├── upload.md            ← File upload context
│       ├── ocr_nlp.md           ← OCR + NLP extraction context
│       ├── timeline.md          ← Timeline builder context
│       ├── rag.md               ← Legal RAG research engine context
│       ├── similarity.md        ← Case similarity context
│       ├── contradiction.md     ← Contradiction detection context
│       ├── blockchain.md        ← Blockchain ledger context
│       └── frontend.md          ← Frontend + UI context
│
├── backend/                     ← Python FastAPI
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── requirements.txt
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── middleware/
│   └── data/
│
└── frontend/                    ← Next.js 14 + shadcn/ui
    └── src/
        ├── app/
        ├── components/
        ├── lib/
        ├── hooks/
        └── types/
```

---

## Tech Stack (Confirmed)

### Backend
| Layer | Technology | Why |
|---|---|---|
| Framework | FastAPI (Python) | Async, auto OpenAPI docs, fast |
| Database | MongoDB (motor async) | Flexible documents for case/entity data |
| Auth | JWT (python-jose) + bcrypt (passlib) | Stateless, secure |
| LLM | OpenAI GPT-4o | Best reasoning for legal tasks |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` | Free, local, CPU-compatible |
| Vector store | ChromaDB | Native metadata filtering by case_id |
| RAG framework | LangChain LCEL | Modern chain composition |
| PDF extraction | PyMuPDF + pymupdf4llm | Fast, Markdown output for RAG |
| OCR | Tesseract + pytesseract | For scanned PDFs and images |
| DOCX | python-docx | Word document support |
| NLP / NER | spaCy + EntityRuler | Deterministic legal patterns |
| NLI (contradiction) | cross-encoder/nli-deberta-v3-small | Lightweight contradiction classifier |
| Similarity | rank-bm25 + cosine (sentence-transformers) | Hybrid lexical + semantic |
| Blockchain ledger | SQLite + hashlib SHA-256 | Append-only integrity log, zero infra |

### Frontend
| Layer | Technology | Why |
|---|---|---|
| Framework | Next.js 14 (App Router) | SSR, routing, server components |
| UI Library | shadcn/ui + Radix UI | Minimal, professional, accessible |
| Styling | Tailwind CSS | Utility-first, consistent |
| Language | TypeScript | Type safety across components |

---

## Confirmed Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Indian legal corpus | IPC, CrPC, Constitution, Evidence Act, IT Act | Covers criminal + civil + digital law |
| Corpus source | IndiaCode.gov.in | Official government source, free, structured |
| Seeding strategy | Once via `seed.py`, cached permanently in ChromaDB | Avoid re-embedding on every restart |
| RAG search scope | Corpus-only (seeded statutes) | Uploaded docs used only for extraction/contradiction |
| Upload formats | PDF, scanned PDF, DOCX, JPG, PNG | All common legal document types |
| User management | Full multi-user with JWT auth | Each lawyer owns their own cases |
| Contradiction scope | Cross-document within a case | More valuable than within-doc only |
| Dashboard | Card-based per-case overview | See all module outputs at a glance |
| Evidence integrity UI | Full SHA-256 hash + audit log table | Transparency for legal admissibility |
| Main DB | MongoDB | Flexible schema for varied entity types |
| Blockchain | SQLite append-only + SHA-256 | Phase I: no infra overhead; Phase II: Hyperledger |

---

## Phased Delivery Status

| Phase | Name | Status |
|---|---|---|
| **1** | Foundation & Auth | 🔨 In Progress |
| **2** | Document Intelligence (OCR + NLP + Timeline) | ⏳ Pending |
| **3** | Legal RAG Research Engine | ⏳ Pending |
| **4** | Contradiction Detection | ⏳ Pending |
| **5** | Blockchain Evidence Integrity | ⏳ Pending |

---

## API Base URLs

| Environment | Backend | Frontend |
|---|---|---|
| Local dev | `http://localhost:8000` | `http://localhost:3000` |

## Environment Variables

### Backend `.env`
```
OPENAI_API_KEY=sk-...
MONGO_URI=mongodb://localhost:27017
MONGO_DB=casecrypt
JWT_SECRET=your-secret-here
```

### Frontend `.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Key Invariants (Never Break These)

1. **Blockchain ledger is append-only** — no UPDATE or DELETE ever on `ledger.db`
2. **Documents stay off-chain** — only SHA-256 hashes + metadata go to the ledger
3. **Every AI output must cite its source** — no unsupported answers returned to users
4. **Lawyers are always in the loop** — system is decision support, not autonomous
5. **RAG searches corpus only** — it does not mix uploaded case docs into statute retrieval
6. **Each user's cases are isolated** — no cross-user data leakage (always filter by `owner_id`)

---

## How to Run (Phase 1)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env   # fill in your keys
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

---

## Contact

| Name | Roll No | Role |
|---|---|---|
| Niharika Singh | 1DS23IC033 | Team Member |
| Meghana Pise | 1DS23IC026 | Team Member |
| Ashab Khan | 1DS23IC027 | Team Member |
| Aditya Piyush | 1DS23IC002 | Team Member |
| Dr. D. Annapurna | — | Project Guide |
