from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./data/app.db")
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection: str = Field(default="pe_docs")
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim: int = Field(default=384)
    llm_model: str = Field(default="gpt-4o-mini")
    llm_base_url: str = Field(default="https://api.openai.com/v1")
    llm_api_key: str | None = Field(default=None)
    chunk_size: int = Field(default=800, description="Target token-ish length for each chunk")
    chunk_overlap: int = Field(default=100, description="Overlap when chunking to keep context")

    class Config:
        env_file = ".env"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    if settings.database_url.startswith("sqlite:///"):
        data_path = Path(settings.database_url.replace("sqlite:///", ""))
        data_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
