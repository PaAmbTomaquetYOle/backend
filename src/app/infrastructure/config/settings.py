"""Application configuration loaded from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings sourced from environment variables (and an optional .env file)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Slack Agent Backend"
    environment: str = "local"
    log_level: str = "INFO"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "OffBoardMe"
    db_user: str = "postgres"
    db_password: str  # No default — must be set in .env

    # JWT
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_audience: str = "offboardme-backend"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "offboardme-backend"
    kafka_topic_prefix: str = "offboarding"
    kafka_inbound_topic_prefix: str = "slack-agent"
    kafka_consumer_group_id: str = "offboardme-backend-consumer"
    kafka_dlq_topic: str = "offboarding.dlq"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str  # No default — must be set in .env
    neo4j_database: str = "neo4j"

    # AI dossier generation (LLMDossierGenerator) — see IDossierGenerator
    # The model itself lives in mcp-server's `generate_dossier` tool; the
    # backend is just an MCP client of it.
    dossier_llm_enabled: bool = False
    dossier_llm_timeout_seconds: float = 45.0
    mcp_server_url: str = "http://localhost:8000/mcp"

    @property
    def database_url(self) -> str:
        """Assemble the async PostgreSQL connection URL from individual components.

        Returns:
            str: A psycopg-compatible async database URL.
        """
        return f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
