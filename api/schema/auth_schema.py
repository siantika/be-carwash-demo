from datetime import datetime

from pydantic import BaseModel, Field

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
    token_type: str
    user: UserResponse


class TokenResponse(BaseModel):
    """Schema for generic token response."""
    access_token: str
    token_type: str
    
    
class TokenData(BaseModel):
    """
    Internal schema for decoded JWT payload.

    Uses 'sub' as alias for user_id per JWT standards.
    """
    # Internal JWT usually works with 'sub' field name
    user_id: int = Field(alias="sub")
    username: str
    role: str
    exp: int

    class Config:
        """ Base model config """
        populate_by_name = True  # allows access via both 'user_id' and 'sub'
        extra = "forbid"         # rejects additional/unknown fields
