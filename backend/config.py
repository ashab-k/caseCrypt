from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    openai_api_key: str = ""

    # SQLite (persistent file DB)
    sqlite_path: Path = BASE_DIR / "data" / "casecrypt.db"

    # JWT
    jwt_secret: str = "changeme-super-secret-key-casecrypt"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Paths
    upload_dir: Path = BASE_DIR / "data" / "uploads"
    chroma_dir: Path = BASE_DIR / "data" / "chroma_db"
    corpus_dir: Path = BASE_DIR / "data" / "sample_corpus"
    cases_dir: Path = BASE_DIR / "data" / "cases"
    ledger_db: Path = BASE_DIR / "data" / "ledger.db"

    # Models
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gpt-4o"

    # CORS — JSON list or comma-separated string in env
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> Any:
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("["):
                import json

                return json.loads(raw)
            return [part.strip() for part in raw.split(",") if part.strip()]
        return v

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        def abs_path(p: Path) -> Path:
            return p if p.is_absolute() else (BASE_DIR / p).resolve()

        self.sqlite_path = abs_path(self.sqlite_path)
        self.upload_dir = abs_path(self.upload_dir)
        self.chroma_dir = abs_path(self.chroma_dir)
        self.corpus_dir = abs_path(self.corpus_dir)
        self.cases_dir = abs_path(self.cases_dir)
        self.ledger_db = abs_path(self.ledger_db)
        return self


settings = Settings()

# Ensure directories exist on import
for _d in [settings.upload_dir, settings.chroma_dir, settings.corpus_dir, settings.cases_dir]:
    _d.mkdir(parents=True, exist_ok=True)
settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
