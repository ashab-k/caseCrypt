# CaseCrypt

Smart Legal Case Intelligence System — AI/NLP + blockchain evidence integrity for Indian legal professionals.

## Quick start (Docker)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API / docs: http://localhost:8000/docs

After the services start, seed the public statute library once:

```bash
docker compose exec backend python seed.py
```

Then sign in and open **Research**. Without an OpenAI key, it returns cited statute excerpts. IPC, CrPC, and Evidence Act material is labelled historical; see [Phase 3](docs/phases/phase_3.md) for corpus scope and source URLs.

SQLite (`casecrypt.db`) and uploaded files persist in the Docker volume `casecrypt_data`.

Optional env (create a root `.env` or export):

```bash
JWT_SECRET=your-secret
OPENAI_API_KEY=sk-...   # needed from Phase 2+
```

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# macOS OCR: brew install tesseract
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

For local research, also run `venv/bin/python seed.py` inside `backend` once. Seeding downloads public PDFs and local embedding weights; subsequent searches run from the persistent cache.

## Docs

See [`docs/GLOBAL_CONTEXT.md`](docs/GLOBAL_CONTEXT.md) and [`docs/phases/`](docs/phases/) for phased delivery details.
