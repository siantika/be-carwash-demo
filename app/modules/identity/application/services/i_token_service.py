from dataclasses import dataclass

from app.modules.identity.domain.entities.account import RoleCode
from app.modules.identity.domain.value_objects.username import Username


@dataclass(frozen=True)
class ITokenService:
    def create_access_token(self, account_id:str, username:Username, 
                            role: RoleCode, expires:int): ...
    def generate_refresh_token(self): ...
    def hash_refresh_token(self): ...
    
    