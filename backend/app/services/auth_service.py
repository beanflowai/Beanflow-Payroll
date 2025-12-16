"""Authentication service for Supabase Auth"""

import logging
from typing import Any

from app.core.security import verify_supabase_jwt
from app.core.supabase_client import get_supabase_client
from app.models.auth import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    def verify_token(token: str) -> dict[str, Any] | None:
        """Verify a Supabase JWT token

        Args:
            token: JWT access token

        Returns:
            Decoded token payload or None if invalid
        """
        return verify_supabase_jwt(token)

    @staticmethod
    def get_user_from_payload(payload: dict[str, Any]) -> UserResponse:
        """Extract user information from JWT payload

        Args:
            payload: Decoded JWT payload

        Returns:
            UserResponse with user information
        """
        user_metadata = payload.get("user_metadata", {})

        return UserResponse(
            id=payload.get("sub", ""),
            email=payload.get("email"),
            full_name=user_metadata.get("full_name") or user_metadata.get("name"),
            avatar_url=user_metadata.get("avatar_url") or user_metadata.get("picture"),
        )

    @staticmethod
    async def get_user_by_id(user_id: str) -> UserResponse | None:
        """Get user information from Supabase Auth

        Args:
            user_id: Supabase user ID

        Returns:
            UserResponse or None if not found
        """
        try:
            client = get_supabase_client()
            response = client.auth.admin.get_user_by_id(user_id)

            if response and response.user:
                user = response.user
                user_metadata = user.user_metadata or {}

                return UserResponse(
                    id=user.id,
                    email=user.email,
                    full_name=user_metadata.get("full_name") or user_metadata.get("name"),
                    avatar_url=user_metadata.get("avatar_url") or user_metadata.get("picture"),
                    created_at=user.created_at,
                    last_sign_in_at=user.last_sign_in_at,
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None


# Singleton instance
auth_service = AuthService()
