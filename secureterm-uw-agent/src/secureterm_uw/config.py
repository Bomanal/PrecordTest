"""Runtime configuration. Open items are never defaulted into business rules."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parent
DEFAULT_PRECORD = REPO_ROOT / "precord-TestLifeUW SecureTerm UW-candidate"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SECURETERM_", extra="ignore")

    precord_path: Path = DEFAULT_PRECORD
    environment: str = "development"
    mock_gateway: bool = True
    api_gateway_base_url: str = "http://localhost:8080"
    oauth_token_url: str = ""
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    correlation_id_header: str = "x-correlation-id"
    otlp_endpoint: str = ""
    log_sink: str = ""
    model_name: str = "gemini-3.5-flash"
    model_temperature: float = 0.2
    llm_enabled: bool = False
    data_residency_zone: str = "in-approved-zone"
    session_idle_timeout_s: int = 1800
    host: str = "127.0.0.1"
    port: int = 8000


def get_settings() -> Settings:
    return Settings()
