"""Central configuration loaded from environment variables.

Every external service has a `*_MODE` switch ('mock' vs 'real'). Modules read
the mode and dispatch to the right adapter — we can run the full pipeline
offline with zero API keys, or wire up real integrations one at a time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Mode = Literal["mock", "real"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Anthropic
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    claude_mode: Mode = "mock"

    # Google Places
    google_places_api_key: str = ""
    places_mode: Mode = "mock"

    # Airtable / SQLite
    airtable_api_key: str = ""
    airtable_base_id: str = ""
    storage_backend: Literal["sqlite", "airtable"] = "sqlite"
    sqlite_path: Path = Path("data/pipeline.sqlite")

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_mode: Mode = "mock"

    # Gmail
    gmail_credentials_path: str = ""
    gmail_token_path: str = ""
    gmail_mode: Mode = "mock"

    # Mock fixtures
    mock_places_fixture: Path = Path("data/fixtures/places.json")
    mock_sms_fixture: Path = Path("data/fixtures/sms_responses.json")
    mock_email_fixture: Path = Path("data/fixtures/email_responses.json")
    mock_classifications_fixture: Path = Path("data/fixtures/classifications.json")

    # General
    log_level: str = "INFO"
    report_output_dir: Path = Field(default=Path("reports"))


def get_settings() -> Settings:
    return Settings()
