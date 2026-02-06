from dataclasses import dataclass
from enum import Enum
from typing import Optional

from domain.entities.base import BaseEntity
from domain.exceptions import BusinessRuleViolation


class UserRoleEnum(str, Enum):
    CASHIER = "CASHIER"
    ADMIN = "ADMIN"


@dataclass(kw_only=True)
class User(BaseEntity):
    id: int
    username: str
    password_hash: Optional[str] = None 
    role: UserRoleEnum
    is_active: bool = True

    def __post_init__(self) -> None :
        if not self.username:
            raise BusinessRuleViolation("Username must not be empty")

    # --- Domain behaviours ---
    def has_role(self, role: UserRoleEnum) -> bool:
        return self.role == role

    def is_admin(self) -> bool:
        return self.role == UserRoleEnum.ADMIN

    def is_cashier(self) -> bool:
        return self.role == UserRoleEnum.CASHIER
    
    def activate(self) -> None:
        self.is_active = True 
        
    def deactivate(self) -> None:
        self.is_active = False 
