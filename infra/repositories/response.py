from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

""" args must be in this order (BaseModel first)"""
class BaseResponse(BaseModel, Generic[T]):
    status: str
    message: Optional[str] = None
    data: Optional[T] = None

class BaseErrorResponse(BaseModel):
    status: str 
    message: Optional[str] = None 
    error_type: str
     