from typing import Any, Protocol


class IRequestHasher(Protocol):
    def hash(self, payload: dict[str, Any]) -> str: ...

