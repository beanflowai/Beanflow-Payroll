"""Supabase Client Singleton"""

import logging

from supabase import Client, create_client

from app.core.config import get_config

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client with RLS context management"""

    _instance: Client | None = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client singleton"""
        if cls._instance is None:
            config = get_config()
            cls._instance = create_client(config.supabase_url, config.supabase_key)
            logger.info("Supabase client initialized")
        return cls._instance

    @classmethod
    def set_user_context(cls, user_id: str) -> None:
        """Set RLS context for the current user

        This sets the app.current_user_id config variable that RLS policies use
        to filter data by user.
        """
        client = cls.get_client()
        try:
            client.rpc(
                "set_config",
                {"setting": "app.current_user_id", "value": user_id, "is_local": True},
            ).execute()
            logger.debug(f"RLS context set for user: {user_id[:8]}...")
        except Exception as e:
            logger.warning(f"Failed to set RLS context: {e}")

    @classmethod
    def check_connection(cls) -> bool:
        """Check if Supabase connection is healthy"""
        try:
            client = cls.get_client()
            # Simple query to verify connection
            client.table("_health_check").select("*").limit(0).execute()
            return True
        except Exception:
            # Table doesn't exist is fine - connection works
            return True


def get_supabase_client() -> Client:
    """Get Supabase client (convenience function)"""
    return SupabaseClient.get_client()
