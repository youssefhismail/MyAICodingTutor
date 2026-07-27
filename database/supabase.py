"""Supabase client factory."""

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL


def get_supabase_client() -> Client:
    """Create a configured Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)
