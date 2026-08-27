"""
NidhiPath — Application Configuration

Loads environment variables from .env file at the project root.
All config is centralized here — no other module should read os.environ directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (two levels up from backend/app/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Application settings loaded from environment variables."""

    # --- Supabase ---
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # --- Direct Postgres ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # --- Groq ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "gpt-oss-120b")

    # --- App ---
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    ]
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # --- Data directory ---
    DATA_DIR: Path = PROJECT_ROOT / os.getenv("DATA_DIR", "data")

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def has_supabase(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_ANON_KEY)

    @property
    def has_database(self) -> bool:
        return bool(self.DATABASE_URL)

    @property
    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY)


settings = Settings()
