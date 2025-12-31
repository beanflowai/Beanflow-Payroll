"""Health check endpoint"""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app import __version__
from app.core.config import get_config
from app.core.supabase_client import SupabaseClient
from app.models.schemas import HealthCheckResponse
from app.utils.response import create_success_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=None)
async def health_check() -> JSONResponse:
    """Health check endpoint

    Returns:
        Health status including Supabase connection status
    """
    config = get_config()

    # Check Supabase connection
    supabase_status = "connected" if SupabaseClient.check_connection() else "disconnected"

    health_data = HealthCheckResponse(
        status="healthy",
        version=__version__,
        supabase=supabase_status,
        debug=config.debug,
    )

    return create_success_response(health_data.model_dump())
