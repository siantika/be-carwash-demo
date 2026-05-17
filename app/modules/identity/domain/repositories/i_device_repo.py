from typing import Protocol

from app.modules.identity.domain.entities.device import Device


class IDeviceRepository(Protocol):
    async def find_by_code(self, device_code: str) -> Device | None: ...

    async def touch_last_seen(self, device_id: int) -> None: ...
