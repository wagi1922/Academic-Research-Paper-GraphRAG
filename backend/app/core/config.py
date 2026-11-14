from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="graphrag123", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    # LLM / Embedding (OpenRouter via 9router)
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    llm_model: str = Field(default="openrouter/gpt-4o-mini", alias="LLM_MODEL")
    embedding_model: str = Field(default="openrouter/nomic-embed-text", alias="EMBEDDING_MODEL")

    # Ollama (local fallback)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_embed_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")

    # PDF Parser
    grobid_url: str = Field(default="http://localhost:8070/api/processFulltextDocument", alias="GROBID_URL")
    # llamaparse_api_key: Optional[str] = Field(default=None, alias="LLAMAPARSE_API_KEY")

    # App
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Ingestion defaults
    default_chunk_size: int = 512
    default_chunk_overlap: int = 50
    default_top_k: int = 5
    default_depth: int = 2

    # CORS
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()