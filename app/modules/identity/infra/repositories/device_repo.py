import asyncpg

from app.modules.identity.domain.entities.device import Device
from app.modules.identity.domain.repositories.i_device_repo import IDeviceRepository
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger

SELECT_ALL_COLUMNS = """
id,
device_code,
name,
location,
is_active,
last_seen_at,
created_at,
updated_at
""".strip()


def _mapper(row: asyncpg.Record) -> Device:
    return Device(
        id=row["id"],
        device_code=row["device_code"],
        name=row["name"],
        location=row["location"],
        is_active=row["is_active"],
        last_seen_at=row["last_seen_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncPgDeviceRepository(IDeviceRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def find_by_code(self, device_code: str) -> Device | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM identity.devices
                WHERE device_code = $1;
                """,
                device_code,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"device_code": device_code},
            operation_name="fetch device by code",
        )

    async def touch_last_seen(self, device_id: int) -> None:
        async def _update():
            await self.db.execute(
                """
                UPDATE identity.devices
                SET last_seen_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1;
                """,
                device_id,
            )
            return None

        await handle_db_error(
            operation=_update,
            logger=self.logger,
            context={"device_id": device_id},
            operation_name="update device last_seen_at",
        )
