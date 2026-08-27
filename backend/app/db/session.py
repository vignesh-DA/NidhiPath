"""
NidhiPath — Database Session Management

Provides Supabase client when configured, otherwise falls back to direct
Postgres connection. For Modules 1-3 (demo phase), data is loaded directly
from JSON files — no database dependency required.
"""

from typing import Optional
from app.config import settings

# Lazy-initialized clients
_supabase_client = None


def get_supabase_client():
    """
    Returns a Supabase client instance (singleton).
    Returns None if Supabase is not configured.
    """
    global _supabase_client

    if not settings.has_supabase:
        return None

    if _supabase_client is None:
        from supabase import create_client
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY,
        )

    return _supabase_client


def get_supabase_client_or_raise():
    """
    Returns a Supabase client or raises an error.
    Use this for endpoints that strictly require Supabase (e.g., Module 4 RAG with pgvector).
    """
    client = get_supabase_client()
    if client is None:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env"
        )
    return client
