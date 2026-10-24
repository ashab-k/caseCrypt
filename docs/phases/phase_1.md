# Phase 1 — Foundation & Auth

> **Status**: 🔨 In Progress
> **Goal**: Working full-stack skeleton — register, login, create cases, upload files.
> **Depends on**: Nothing (this is the base layer)
> **Unlocks**: All other phases (phases 2–5 plug into this skeleton)

---

## What This Phase Builds

| Area | What |
|---|---|
| **Backend** | FastAPI app, MongoDB connection, JWT auth (register/login/me), case CRUD, file upload endpoint |
| **Frontend** | Next.js 14 + shadcn/ui setup, landing page, login/register pages, dashboard (empty module cards), case creation dialog, file upload drag-and-drop |
| **Infra** | `.env` config, CORS middleware, MongoDB indexes, folder structure |

---

## Backend Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, CORS, lifespan (DB connect/close), router registration |
| `config.py` | Settings via pydantic-settings, reads from `.env` |
| `database.py` | Motor async MongoDB client, connect/close, index creation |
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

## MongoDB Collections

### `users`
```json
{
  "_id": ObjectId,
  "name": "string",
  "email": "string (unique)",
  "password_hash": "string (bcrypt)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `cases`
```json
{
  "_id": ObjectId,
  "title": "string",
  "description": "string",
  "case_type": "criminal | civil | contract | other",
  "owner_id": "string (user _id)",
  "document_count": 0,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `documents`
```json
{
  "_id": ObjectId,
  "case_id": "string",
  "owner_id": "string",
  "filename": "uuid_originalname.pdf",
  "original_name": "FIR_Case123.pdf",
  "file_type": "pdf | docx | jpg | png",
  "file_size": 204800,
  "sha256": "abc123...",
  "uploaded_at": "datetime",
  "extracted": false
}
```

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

- [ ] User can register and receive a JWT
- [ ] User can login and receive a JWT
- [ ] Protected routes return 401 without valid JWT
- [ ] User can create a case (criminal/civil/contract/other)
- [ ] User can list only their own cases
- [ ] User can upload PDF, DOCX, JPG, PNG to a case
- [ ] Uploaded files appear in the documents list for that case
- [ ] Frontend login/register forms work and store JWT in localStorage
- [ ] Dashboard shows all user cases as cards
- [ ] `npm run build` passes with 0 errors
- [ ] `uvicorn main:app` starts without errors

---

## Known Limitations (Addressed in Later Phases)

- File upload stores the file but does NOT yet hash it to the blockchain ledger (Phase 5)
- File upload does NOT yet trigger OCR/NLP extraction (Phase 2)
- Case detail page shows empty module cards — populated in phases 2–5
