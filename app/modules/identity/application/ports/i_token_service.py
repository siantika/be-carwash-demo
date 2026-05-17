from typing import Protocol

from app.modules.identity.domain.entities.account import RoleCode
from app.modules.identity.domain.value_objects.username import Username


class ITokenService(Protocol):
    def create_access_token(
        self,
        account_id: str,
        username: Username,
        role: RoleCode,
        expires: int,
    ) -> str: ...

    def generate_refresh_token(self) -> str: ...

    def hash_refresh_token(self, token: str) -> str: ...
