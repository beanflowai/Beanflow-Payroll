"""Authentication endpoints"""

import logging

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.utils.response import create_success_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=None)
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user information

    Args:
        current_user: Injected current user from JWT token

    Returns:
        User information
    """
    return create_success_response(current_user.model_dump(mode="json"))


@router.post("/logout", response_model=None)
async def logout(current_user: CurrentUser):
    """Logout endpoint

    Note: Since we use Supabase Auth, actual logout is handled client-side.
    This endpoint can be used to perform server-side cleanup if needed.

    Args:
        current_user: Injected current user from JWT token

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.id[:8]}...")
    return create_success_response({"message": "Logged out successfully"})
