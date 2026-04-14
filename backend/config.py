from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    workspace_root: str = Field(default="./workspace")
    database_url: str = Field(default="sqlite:///./workspace/sqlite/pe_core.db")
    duckdb_path: str = Field(default="./workspace/duckdb/pe_analytics.duckdb")
    mempalace_root: str = Field(default="./workspace/mempalace")
    deals_root: str = Field(default="./workspace/deals")
    skills_root: str = Field(default="./workspace/skills")
    templates_root: str = Field(default="./workspace/templates")
    postmortems_root: str = Field(default="./workspace/postmortems")
    cache_root: str = Field(default="./workspace/cache")
    logs_root: str = Field(default="./workspace/logs")
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection: str = Field(default="pe_docs")
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim: int = Field(default=384)
    llm_provider: str = Field(
        default="openai_compatible",
        description="Use 'openai_compatible' for local vLLM/Ollama gateways or 'provider' for hosted APIs.",
    )
    llm_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct")
    llm_base_url: str = Field(default="http://localhost:8001/v1")
    llm_api_key: str | None = Field(default=None)
    neo4j_uri: str | None = Field(default="bolt://localhost:7687")
    neo4j_username: str = Field(default="neo4j")
    neo4j_password: str = Field(default="pe-memory-password")
    connectors_root: str = Field(default="./workspace/connectors")
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
    for root in (
        settings.workspace_root,
        settings.deals_root,
        settings.skills_root,
        settings.templates_root,
        settings.postmortems_root,
        settings.cache_root,
        settings.logs_root,
        settings.mempalace_root,
        settings.connectors_root,
    ):
        Path(root).mkdir(parents=True, exist_ok=True)
    Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)
    return settings
