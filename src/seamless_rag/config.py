"""Pydantic Settings — environment variables and .env file configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Seamless-RAG configuration from environment variables."""

    # MariaDB
    mariadb_host: str = Field(default="127.0.0.1", alias="MARIADB_HOST")
    mariadb_port: int = Field(default=3306, alias="MARIADB_PORT")
    mariadb_user: str = Field(default="root", alias="MARIADB_USER")
    mariadb_password: str = Field(default="seamless", alias="MARIADB_PASSWORD")
    mariadb_database: str = Field(default="seamless_rag", alias="MARIADB_DATABASE")

    # Embedding
    embedding_provider: str = Field(default="sentence-transformers", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=384, alias="EMBEDDING_DIMENSIONS")

    # Watch mode
    watch_interval: float = Field(default=2.0, alias="WATCH_INTERVAL")
    watch_batch_size: int = Field(default=64, alias="WATCH_BATCH_SIZE")
    watch_max_retries: int = Field(default=3, alias="WATCH_MAX_RETRIES")

    # LLM (for RAG answer generation)
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str = Field(default="llama3", alias="LLM_MODEL")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
