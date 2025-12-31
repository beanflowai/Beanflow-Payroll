"""Base response schemas"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response model"""

    success: bool


class SuccessResponse(BaseResponse, Generic[T]):
    """Success response with data"""

    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseResponse):
    """Error response"""

    success: bool = False
    error: str
    details: str | None = None


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    supabase: str
    debug: bool


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response"""

    success: bool = True
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
