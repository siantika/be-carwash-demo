from typing import Protocol

from app.modules.identity.domain.value_objects.plain_password import PlainPassword


class IPasswordHasher(Protocol):
    def verify(self, plain_password:PlainPassword, hashed_password:str): ... 
    
    
    