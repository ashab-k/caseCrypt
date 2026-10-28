"""
CaseCrypt Backend — FastAPI entrypoint
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import close_db, connect_db
from routers import auth, cases, extract, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="CaseCrypt API",
    description="Smart Legal Case Intelligence System — AI/NLP + Blockchain Evidence Integrity",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(upload.router, prefix="/api/cases", tags=["Upload"])
# Phase 2 routers
app.include_router(extract.router, prefix="/api/cases", tags=["Extract"])


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "CaseCrypt API", "version": "1.0.0"}
