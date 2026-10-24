from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "casecrypt"

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

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist on import
for _d in [settings.upload_dir, settings.chroma_dir, settings.corpus_dir, settings.cases_dir]:
    _d.mkdir(parents=True, exist_ok=True)
