"""FastAPI Dependencies for authentication and authorization"""

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.security import verify_supabase_jwt
from app.core.supabase_client import SupabaseClient
from app.models.auth import UserResponse

logger = logging.getLogger(__name__)


def extract_bearer_token(authorization: str | None) -> str | None:
    """Extract bearer token from Authorization header"""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> UserResponse:
    """Get current authenticated user from JWT token

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        UserResponse with user information

    Raises:
        HTTPException: If authentication fails
    """
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify JWT token
    payload = verify_supabase_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Set RLS context for database queries
    SupabaseClient.set_user_context(user_id)

    # Get user metadata from token
    user_metadata = payload.get("user_metadata", {})

    return UserResponse(
        id=user_id,
        email=payload.get("email"),
        full_name=user_metadata.get("full_name") or user_metadata.get("name"),
        avatar_url=user_metadata.get("avatar_url") or user_metadata.get("picture"),
    )


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
) -> UserResponse | None:
    """Get current user if authenticated, otherwise return None

    Use this for endpoints that work with or without authentication.
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


# Type aliases for dependency injection
CurrentUser = Annotated[UserResponse, Depends(get_current_user)]
OptionalUser = Annotated[UserResponse | None, Depends(get_optional_user)]
