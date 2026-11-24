from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="graphrag123", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    # LLM (OpenRouter FREE models only — NO PAID). Embeddings: local MiniLM via guard-embedding.service.
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    llm_model: str = Field(default="nvidia/nemotron-3.5-lightning:free", alias="LLM_MODEL")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    embedding_url: str = Field(default="http://localhost:8788", alias="EMBEDDING_URL")

    # PDF Parser
    grobid_url: str = Field(default="http://localhost:8070/api/processFulltextDocument", alias="GROBID_URL")

    # App
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Ingestion defaults
    default_chunk_size: int = 512
    default_chunk_overlap: int = 50
    default_top_k: int = 5
    default_depth: int = 2

    # CORS - store as string, parse to list via property
    cors_origins_raw: str = Field(default="*", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        if self.cors_origins_raw == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    class Config:
        env_file = "/home/guard/Documents/perkuliahan/sem 7/Cap/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()