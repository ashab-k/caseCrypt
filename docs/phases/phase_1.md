# Phase 1 — Foundation & Auth

> **Status**: 🔨 In Progress
> **Goal**: Working full-stack skeleton — register, login, create cases, upload files.
> **Depends on**: Nothing (this is the base layer)
> **Unlocks**: All other phases (phases 2–5 plug into this skeleton)

---

## What This Phase Builds

| Area | What |
|---|---|
| **Backend** | FastAPI app, persistent SQLite (SQLAlchemy), JWT auth (register/login/me), case CRUD, file upload endpoint |
| **Frontend** | Next.js App Router, landing page, login/register pages, dashboard, case creation, file upload drag-and-drop |
| **Infra** | `.env` config, CORS middleware, Docker Compose (backend + frontend), named volume for SQLite + uploads |

---

## Backend Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, CORS, lifespan (DB connect/close), router registration |
| `config.py` | Settings via pydantic-settings, reads from `.env` |
| `database.py` | Async SQLAlchemy engine + session factory, SQLite file create/connect |
| `models/orm.py` | SQLAlchemy ORM tables: users, cases, documents |
| `middleware/auth.py` | JWT token creation, `get_current_user` dependency |
| `models/user.py` | UserCreate, UserLogin, UserOut, TokenResponse |
| `models/case.py` | CaseCreate, CaseUpdate, CaseOut, DocumentOut |
| `routers/auth.py` | POST /auth/register, /auth/login, GET /auth/me |
| `routers/cases.py` | GET/POST/PUT/DELETE /cases |
| `routers/upload.py` | POST /cases/{id}/upload (multipart) |

---

## API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | None | Create account, returns JWT |
| POST | `/api/auth/login` | None | Login, returns JWT |
| GET | `/api/auth/me` | JWT | Return current user |

### Cases
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/cases` | JWT | Create a new case |
| GET | `/api/cases` | JWT | List all cases for current user |
| GET | `/api/cases/{id}` | JWT | Get case by ID |
| PUT | `/api/cases/{id}` | JWT | Update case title/description/type |
| DELETE | `/api/cases/{id}` | JWT | Delete case + all files |

### Upload
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/cases/{id}/upload` | JWT | Upload file(s) to a case |
| GET | `/api/cases/{id}/documents` | JWT | List all documents in a case |
| DELETE | `/api/cases/{id}/documents/{doc_id}` | JWT | Delete a document |

---

## SQLite Tables (`data/casecrypt.db`)

### `users`
| Column | Type |
|---|---|
| id | TEXT PK (UUID) |
| name | TEXT |
| email | TEXT UNIQUE |
| password_hash | TEXT (bcrypt) |
| created_at / updated_at | DATETIME |

### `cases`
| Column | Type |
|---|---|
| id | TEXT PK (UUID) |
| title / description | TEXT |
| case_type | TEXT (`criminal \| civil \| contract \| other`) |
| owner_id | TEXT FK → users.id |
| document_count | INTEGER |
| created_at / updated_at | DATETIME |

### `documents`
| Column | Type |
|---|---|
| id | TEXT PK (UUID) |
| case_id / owner_id | TEXT FK |
| filename / original_name | TEXT |
| file_type | TEXT |
| file_size | INTEGER |
| sha256 | TEXT |
| uploaded_at | DATETIME |
| extracted | BOOLEAN |

> Blockchain ledger remains a **separate** append-only file: `data/ledger.db` (Phase 5).

---

## Frontend Pages

| Page | Route | Description |
|---|---|---|
| Landing | `/` | Hero, features overview, CTA to register |
| Register | `/register` | Name, email, password form |
| Login | `/login` | Email, password form |
| Dashboard | `/dashboard` | All cases as cards, create new case button |
| Case Detail | `/cases/[id]` | Empty module cards (timeline, RAG, etc.) |
| Upload | `/cases/[id]/upload` | Drag-and-drop file zone |

---

## Deliverable / Definition of Done

- [x] User can register and receive a JWT
- [x] User can login and receive a JWT
- [x] Protected routes return 401 without valid JWT
- [x] User can create a case (criminal/civil/contract/other)
- [x] User can list only their own cases
- [x] User can upload PDF, DOCX, JPG, PNG to a case
- [x] Uploaded files appear in the documents list for that case
- [x] Frontend login/register forms work and store JWT in localStorage
- [x] Dashboard shows all user cases as cards
- [x] `npm run build` passes with 0 errors
- [x] `uvicorn main:app` starts without errors
- [x] Dockerfiles + `docker compose` defined (backend + frontend + persistent volume)
- [x] SQLite DB path + uploads designed for named volume persistence (`casecrypt_data`)

---

## Known Limitations (Addressed in Later Phases)

- File upload stores the file but does NOT yet hash it to the blockchain ledger (Phase 5)
- File upload does NOT yet trigger OCR/NLP extraction (Phase 2)
- Case detail page shows empty module cards — populated in phases 2–5
