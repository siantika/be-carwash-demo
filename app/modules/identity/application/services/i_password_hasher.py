from typing import Protocol


class IPasswordHasher(Protocol):
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...
