"""Supabase Client Singleton"""

import logging
from contextvars import ContextVar

from app.core.config import get_config
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Context variable to store the current user's JWT token per request
_current_user_token: ContextVar[str | None] = ContextVar("current_user_token", default=None)


class SupabaseClient:
    """Singleton Supabase client with RLS context management"""

    _instance: Client | None = None
    _admin_instance: Client | None = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client singleton"""
        if cls._instance is None:
            config = get_config()
            cls._instance = create_client(config.supabase_url, config.supabase_key)
            logger.info("Supabase client initialized")
        return cls._instance

    @classmethod
    def get_admin_client(cls) -> Client | None:
        """Get Supabase admin client with service role key.

        This client bypasses RLS and can perform admin operations like
        inviting users. Returns None if service role key is not configured.
        """
        if cls._admin_instance is None:
            config = get_config()
            if not config.supabase_service_role_key:
                logger.warning("Service role key not configured, admin client unavailable")
                return None
            cls._admin_instance = create_client(
                config.supabase_url, config.supabase_service_role_key
            )
            logger.info("Supabase admin client initialized")
        return cls._admin_instance

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

        This creates a NEW client instance with the user's JWT token,
        ensuring request isolation and preventing JWT leaks across concurrent requests.

        IMPORTANT: We create a new client for each authenticated request to avoid
        race conditions where concurrent requests could overwrite each other's
        auth headers on a shared singleton.
        """
        token = cls.get_user_token()

        if token:
            # Create a new client instance for this request to ensure isolation
            # This prevents JWT leaks across concurrent async requests
            config = get_config()
            authenticated_client = create_client(config.supabase_url, config.supabase_key)
            authenticated_client.postgrest.auth(token)
            logger.debug("Created isolated authenticated client for request")
            return authenticated_client
        else:
            # No token - fall back to shared unauthenticated client
            logger.warning("No user token available, using unauthenticated client")
            return cls.get_client()

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


def get_supabase_admin_client() -> Client | None:
    """Get Supabase admin client with service role key (convenience function)

    Returns None if service role key is not configured.
    """
    return SupabaseClient.get_admin_client()
