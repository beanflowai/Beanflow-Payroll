"""Response utility functions"""

from typing import Any

from fastapi.responses import JSONResponse


def create_success_response(
    data: Any,
    message: str | None = None,
    status_code: int = 200,
) -> JSONResponse:
    """Create a standardized success response

    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default 200)

    Returns:
        JSONResponse with standardized format
    """
    content: dict[str, Any] = {"success": True, "data": data}
    if message:
        content["message"] = message
    return JSONResponse(content=content, status_code=status_code)


def create_error_response(
    error: str,
    details: str | None = None,
    status_code: int = 400,
) -> JSONResponse:
    """Create a standardized error response

    Args:
        error: Error message
        details: Optional error details
        status_code: HTTP status code (default 400)

    Returns:
        JSONResponse with standardized format
    """
    content: dict[str, Any] = {"success": False, "error": error}
    if details:
        content["details"] = details
    return JSONResponse(content=content, status_code=status_code)
