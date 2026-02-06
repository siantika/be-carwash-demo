from typing import Protocol


class IUseCase(Protocol):
    async def execute(): ...