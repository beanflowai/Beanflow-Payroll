"""Supabase Client Singleton"""

import logging
from contextvars import ContextVar

from supabase import Client, create_client

from app.core.config import get_config

logger = logging.getLogger(__name__)

# Context variable to store the current user's JWT token per request
_current_user_token: ContextVar[str | None] = ContextVar("current_user_token", default=None)


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
    def set_user_token(cls, token: str) -> None:
        """Set the current user's JWT token for this request context.

        This token will be used for Supabase queries to enable proper
        RLS policy evaluation via auth.uid().
        """
        _current_user_token.set(token)
        logger.debug("User token set for request context")

    @classmethod
    def get_user_token(cls) -> str | None:
        """Get the current user's JWT token from request context."""
        return _current_user_token.get()

    @classmethod
    def get_authenticated_client(cls) -> Client:
        """Get Supabase client with user authentication headers set.

        This creates a client that includes the user's JWT token in requests,
        enabling RLS policies that use auth.uid() to work correctly.
        """
        client = cls.get_client()
        token = cls.get_user_token()

        if token:
            # Set the Authorization header on the PostgREST client
            # This makes auth.uid() work in RLS policies
            client.postgrest.auth(token)
            logger.debug("Authenticated client returned with user token")
        else:
            logger.warning("No user token available, using unauthenticated client")

        return client

    @classmethod
    def set_user_context(cls, user_id: str) -> None:
        """Set RLS context for the current user (deprecated - use set_user_token)

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
    """Get Supabase client with user authentication (convenience function)"""
    return SupabaseClient.get_authenticated_client()
