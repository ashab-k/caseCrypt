# Phase 3 — Legal RAG Research Engine

> **Status:** Implemented; local corpus seeded and offline path verified. Live GPT-4o synthesis requires an OpenAI key and has not been exercised against the paid API.
> **Updated:** 29 October 2026

## Delivered

- Authenticated `/research` workspace with act filters, example questions, expandable verbatim sources, official PDF page links, coverage counts, and the last ten queries in memory for the current visit.
- Research links in the main navigation and case workspace. Research remains a global public-statute service and never reads uploaded case documents.
- Persistent Chroma corpus with CPU `all-MiniLM-L6-v2` embeddings, BM25 + cosine retrieval, and exact act/section matching for explicit references.
- LangChain LCEL composition for retrieval → answer generation. GPT-4o uses strict structured output, source IDs, and exact supporting-quote validation. Missing keys, API failures, refusals, or invalid citations fall back to labelled source excerpts. Unsupported searches return an insufficient-support response.
- Idempotent `seed.py`; forced rebuilds stage vectors before publishing and restore the previous collection if publication fails. Stop the API before a forced replacement. Downloaded PDFs and locally saved model weights persist under `data/sample_corpus`; Chroma persists under `data/chroma_db`.
- PDF heading/parser checks reject empty PDFs, contents-only extraction, and insufficient provision coverage. Each chunk keeps its starting physical PDF page. Inserted lettered provisions are retained; corpus counts therefore differ from the last numbered section.
- Existing React effect lint errors in auth/navigation/dashboard were corrected while adding the research entry points. The frontend uses Next's documented Tailwind PostCSS setup and webpack for production builds; development still uses Turbopack.

## Run

```bash
# Local: install once, then seed before starting the backend.
cd backend
venv/bin/pip install -r requirements.txt
venv/bin/python seed.py
venv/bin/uvicorn main:app --reload --port 8000
```

```bash
# Docker: builds both services; seed once into the shared persistent volume.
docker compose up -d --build
docker compose exec backend python seed.py
```

No network access or model download is needed during ordinary research after seeding. No OpenAI key is required for source excerpts. Set `OPENAI_API_KEY` in the backend environment for synthesis; never put it in a `NEXT_PUBLIC_` variable.

```bash
python seed.py                          # Skip an existing ready index
python seed.py --force                  # Rebuild from cached PDFs; stop API first
python seed.py --act IPC                # Start a partial corpus; UI reports partial coverage
python seed.py --source-dir /path/pdfs  # Use official local copies, with canonical names below
```

Local PDF names: `ipc.pdf`, `crpc.pdf`, `constitution.pdf`, `evidence_act.pdf`, `it_act.pdf`. A forced rebuild reuses these cached files; to update a statute snapshot, replace its PDF from the corresponding official source first. Review any locally supplied edition and applicability before indexing it.

## Verified source snapshots

The original India Code `.nic.in` links timed out. The seed uses verified direct public PDF URLs from the current India Code portal and official government sites:

| Act | Official source |
| --- | --- |
| IPC | [India Code archived IPC](https://indiacode.gov.in/server/api/core/bitstreams/337c7a03-60c6-4953-8dd6-90e65c343629/content) |
| CrPC | [Andhra Pradesh High Court compilation](https://aphc.gov.in/docs/6_20241130054414.pdf) |
| Constitution | [Legislative Department English edition, as on 1 May 2026](https://www.legislative.gov.in/static/uploads/2025/07/c9fe9c9b6840524844316f74bb1c556c.pdf) |
| Evidence Act | [India Code archived Evidence Act](https://indiacode.gov.in/server/api/core/bitstreams/4a3677bf-e488-4689-bf30-6ae29255a3ba/content) |
| IT Act | [India Code English compilation](https://indiacode.gov.in/server/api/core/bitstreams/770a7d02-48f2-4274-bab9-10d0f48ee264/content) |

These are static snapshots, not a complete current-law service. IPC, CrPC and Evidence Act text is explicitly labelled historical. The replacement criminal laws effective from 1 July 2024 are outside this phase's corpus; see the [MHA advisory](https://www.mha.gov.in/sites/default/files/Advisory_01052024.pdf). Case law, state amendments not present in the source editions, and automatic amendment/repeal reconciliation are not covered. Constitution schedules/appendices are not indexed as articles.

## API

All endpoints require the existing JWT bearer authentication. No corpus mutation is exposed over HTTP.

| Method | Endpoint | Behavior |
| --- | --- | --- |
| GET | `/api/corpus/status` | Seeded/partial coverage, per-act passage and provision counts, embedding model and synthesis availability |
| POST | `/api/search` | Retrieved verbatim passages and retrieval mode |
| POST | `/api/query` | Cited synthesis or source excerpts; insufficient support when no source matches |

Request:

```json
{"question":"What is Section 302 IPC?","act":"IPC","top_k":5}
```

`act` is optional: `IPC`, `CrPC`, `Constitution`, `Evidence Act`, or `IT Act`. `question` must contain 3–2000 characters and `top_k` must be 1–10. Explicit numbered queries do not substitute neighbouring provisions. A conflicting selected act or an explicit request for an unindexed replacement law returns no support. Numbered comparisons within one act require every requested provision to be present. Split cross-act comparisons into separate queries. Exact long-provision results are still excerpts, limited by `top_k`; inspect the official PDF for the full provision.

Answers include `answer`, `sources`, `confidence`, `retrieved_chunks`, `generation_mode`, `retrieval_mode`, and `notice`. Source records include citation ID, act, section/article, title, verbatim passage, official URL/page, historical flag, and retrieval score. Confidence describes retrieval match, not legal correctness or a calibrated probability. With synthesis, every returned statement must have a valid source ID and a verbatim supporting quote. That check does not prove that the model's interpretation is correct; lawyer review remains required.

The initial design proposed LLM query expansion and a separate cross-encoder/compression stage. This implementation uses deterministic exact-reference routing and hybrid ranking, retaining full source chunks to avoid discarding legal qualifications. MiniLM is a bi-encoder, not a cross-encoder. Those additional retrieval stages remain future enhancements.

## Validation

```bash
PYTHONPATH=backend backend/venv/bin/python -m unittest discover -s backend/tests -v
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

All 28 backend regressions pass, as do frontend lint, TypeScript, and the webpack production build. The authenticated browser flow was checked with an isolated temporary database, including login, refresh, research, expanded sources, history, and logout.

Offline regressions use real Chroma with deterministic test vectors, plus mocked synthesis to check citation failures without API charges. Local real-corpus smoke queries cover IPC 302, Article 21, Evidence Act 65B, IT Act electronic records, natural-language murder punishment, missing sections, and a second idempotent seed run. Model downloads, official source access, and PDF parsing were also exercised locally. Downloaded corpus/model/vector data is intentionally excluded from Git and Docker build context; seed each deployment's persistent volume separately.
