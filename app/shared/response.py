from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class Metadata(BaseModel):
    page: int | None = None
    limit: int | None = None
    total: int | None = None


class BaseResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    metadata: Optional[Metadata] = None


class BaseErrorResponse(BaseModel):
    error: ErrorResponse
