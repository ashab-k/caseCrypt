import json
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent

_DEFAULT_CORS = "http://localhost:3000,http://127.0.0.1:3000"


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

    # CORS as a plain string so pydantic-settings does not JSON-decode the env var.
    # Accepts comma-separated origins or a JSON array string.
    cors_origins: str = _DEFAULT_CORS

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if not raw:
            return []
        if raw.startswith("["):
            parsed = json.loads(raw)
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [part.strip() for part in raw.split(",") if part.strip()]

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
