"""Configuración por variables de entorno (RNF-POR-01, RNF-SEG-04). Sin secretos en el código."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./eventu.db"
    environment: str = "development"
    log_level: str = "INFO"
    rate_limit_per_minute: int = 60  # Propuesto (SAD §3)
    seed_on_startup: bool = False

    @field_validator("database_url")
    @classmethod
    def _normalize_url(cls, v: str) -> str:
        # Render entrega 'postgres://' o 'postgresql://'; SQLAlchemy necesita el driver psycopg.
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://") :]
        return v or "sqlite:///./eventu.db"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
