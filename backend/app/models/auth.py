"""Authentication-related Pydantic models"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """User information response"""

    id: str
    email: EmailStr | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None
    last_sign_in_at: datetime | None = None

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """JWT token payload from Supabase"""

    sub: str  # User ID
    email: str | None = None
    aud: str  # Audience (should be "authenticated")
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    role: str | None = None  # User role
