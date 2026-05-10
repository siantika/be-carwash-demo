from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.security.token_data import TokenData

USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"


class UserResponse(BaseModel):
    id: int = Field(
        ...,
        ge=1,
        description="Unique identifier of the user"
    )
    username: str = Field(
        ...,
        description="Username of the user"
    )
    role: str = Field(
        ...,
        description="Role assigned to the user"
    )
    created_at: datetime = Field(
        ...,
        description="User creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp (UTC)"
    )

class LoginRequest(BaseModel):
    """Schema for user login request."""
    username: str = Field(..., min_length=3,
                          max_length=30,
                          examples=["user_1", "Surya"],
                          pattern=USERNAME_PATTERN,
                          description="Unique username used for login"
                          )
    password: str = Field(..., 
                    min_length=8,
                    max_length=64,
                    description="User password (minimum 8 characters)"
    )
                          

class LoginResponse(BaseModel):
    """Schema for successful login response."""
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class TokenResponse(BaseModel):
    """Schema for generic token response."""
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        min_length=32,
        description="Refresh token issued by the login or refresh endpoint",
    )
    
    
