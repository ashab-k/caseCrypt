# CaseCrypt — Global Project Context

> **Last updated**: 29 October 2026 — Phases 1–2 complete; Phase 3 implemented (live OpenAI synthesis verification pending).
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
├── docker-compose.yml           ← Backend + frontend; volume for SQLite + uploads
├── README.md
├── docs/
│   ├── REQUIREMENTS.md
│   ├── GLOBAL_CONTEXT.md        ← This file
│   └── phases/                  ← phase_1 … phase_5
│
├── backend/                     ← Python FastAPI + SQLite
│   ├── Dockerfile
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/                  ← Pydantic schemas + ORM
│   ├── routers/
│   ├── middleware/
│   └── data/                    ← casecrypt.db, uploads/ (persisted)
│
└── frontend/                    ← Next.js App Router
    ├── Dockerfile
    └── src/
        ├── app/
        ├── components/
        ├── lib/
        └── types/
```

---

## Tech Stack (Confirmed)

### Backend
| Layer | Technology | Why |
|---|---|---|
| Framework | FastAPI (Python) | Async, auto OpenAPI docs, fast |
| Database | SQLite (SQLAlchemy async + aiosqlite) | Zero-infra, file-persisted; Docker volume mounts for durability |
| Auth | JWT (python-jose) + bcrypt (passlib) | Stateless, secure |
| LLM | OpenAI GPT-4o | Best reasoning for legal tasks |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` | Free, local, CPU-compatible |
| Vector store | ChromaDB | Native metadata filtering by case_id |
| RAG framework | LangChain LCEL | Hybrid BM25 + MiniLM/Chroma retrieval; cited GPT-4o or exact excerpts |
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
| Framework | Next.js 16.4 (App Router) | SSR, routing, server components |
| UI Library | shadcn/ui + Radix UI | Minimal, professional, accessible |
| Styling | Tailwind CSS | Utility-first, consistent |
| Language | TypeScript | Type safety across components |

---

## Confirmed Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Indian legal corpus | IPC, CrPC, Constitution, Evidence Act, IT Act | Covers criminal + civil + digital law |
| Corpus source | India Code + official government PDF mirrors | Verified static snapshots; see Phase 3 source manifest |
| Seeding strategy | Once via `seed.py`, cached permanently in ChromaDB | Avoid re-embedding on every restart |
| RAG search scope | Corpus-only (seeded statutes) | Uploaded docs used only for extraction/contradiction |
| Upload formats | PDF, scanned PDF, DOCX, JPG, PNG | All common legal document types |
| User management | Full multi-user with JWT auth | Each lawyer owns their own cases |
| Contradiction scope | Cross-document within a case | More valuable than within-doc only |
| Dashboard | Card-based per-case overview | See all module outputs at a glance |
| Evidence integrity UI | Full SHA-256 hash + audit log table | Transparency for legal admissibility |
| Main DB | SQLite (`data/casecrypt.db`) | Persistent file DB; simple Docker volume; separate from ledger.db |
| Blockchain | SQLite append-only + SHA-256 | Phase I: no infra overhead; Phase II: Hyperledger |
| Deployment | Docker Compose | Backend + frontend; named volume for DB + uploads |

---

## Phased Delivery Status

| Phase | Name | Status |
|---|---|---|
| **1** | Foundation & Auth | ✅ Complete |
| **2** | Document Intelligence (OCR + NLP + Timeline) | ✅ Complete |
| **3** | Legal RAG Research Engine | ✅ Implemented; offline corpus verified |
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
SQLITE_PATH=data/casecrypt.db
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

## How to Run

### Docker (recommended)

```bash
docker compose up --build
# Frontend → http://localhost:3000
# API docs → http://localhost:8000/docs
# Data persists in Docker volume: casecrypt_data
```

### Local (without Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

---


## Phase 3 research setup

Run `docker compose exec backend python seed.py` once after rebuilding, or `venv/bin/python seed.py` inside `backend` for local development. Open `/research` after logging in. The public statute corpus never includes uploaded case files. Without an OpenAI key, research returns labelled verbatim statute excerpts. IPC, CrPC, and Evidence Act sources are historical; the replacement criminal laws are not in the corpus. See `docs/phases/phase_3.md` for exact source URLs, limits, and verification.

## Contact

| Name | Roll No | Role |
|---|---|---|
| Niharika Singh | 1DS23IC033 | Team Member |
| Meghana Pise | 1DS23IC026 | Team Member |
| Ashab Khan | 1DS23IC027 | Team Member |
| Aditya Piyush | 1DS23IC002 | Team Member |
| Dr. D. Annapurna | — | Project Guide |
