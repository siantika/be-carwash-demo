from pydantic import BaseModel, Field


class TokenData(BaseModel):
    """
    Internal schema for decoded JWT payload.

    Uses 'sub' as alias for user_id per JWT standards.
    """

    user_id: int = Field(alias="sub")
    username: str
    role: str
    exp: int

    class Config:
        populate_by_name = True
        extra = "forbid"
