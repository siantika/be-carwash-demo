from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.identity.domain.entities.user import UserRoleEnum


class CreateUserRequest(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        examples=["user01", "cashier01"],
        description="Unique username for login"
    )

    plain_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        repr=False,
        description="Plain password (will be hashed on the server)"
    )

    role: UserRoleEnum = Field(
        ...,
        examples=["CASHIER"],
        description="Role assigned to the user"
    )

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True
    )
