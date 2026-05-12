from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.identity.domain.entities.account import RoleCode

USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"


class AccountResponse(BaseModel):
    id: int = Field(
        ...,
        ge=1,
        description="Unique identifier of the account"
    )
    username: str = Field(
        ...,
        description="Username of the account"
    )
    email: str = Field(
        ...,
        description="Email address of the account"
    )
    role: str = Field(
        ...,
        description="Role assigned to the account"
    )
    is_active: bool = Field(
        ...,
        description="Whether the account can authenticate"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp in UTC"
    )
    updated_at: datetime = Field(
        ...,
        description="Last account update timestamp in UTC"
    )


class RegisterAccountRequest(BaseModel):
    """Schema for registering a new account."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        examples=["cashier_01"],
        pattern=USERNAME_PATTERN,
        description="Unique username used for login",
    )
    email: str = Field(
        ...,
        max_length=255,
        examples=["cashier@example.com"],
        description="Account email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Account password",
    )
    role: RoleCode = Field(
        ...,
        description="Role assigned to the account",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the account can authenticate",
    )

    class Config:
        extra = "forbid"


class LoginRequest(BaseModel):
    """Schema for account login request."""
    username: str = Field(..., min_length=3,
                          max_length=30,
                          examples=["user_1", "Surya"],
                          pattern=USERNAME_PATTERN,
                          description="Unique username used for login"
                          )
    password: str = Field(..., 
                    min_length=8,
                    max_length=64,
                    description="Account password"
    )
                          

class TokenResponse(BaseModel):
    """Schema for token pair response."""
    access_token: str
    refresh_token: str
    token_type: str


class LoginResponse(TokenResponse):
    """Schema for successful login response."""


class CurrentUserResponse(BaseModel):
    user_id: int
    username: str
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        min_length=32,
        description="Refresh token issued by the login or refresh endpoint",
    )
    
    
