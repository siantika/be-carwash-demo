from typing import Any, Mapping

import asyncpg

from app.modules.service_catalog.domain.entities.service_type import ServiceType
from app.modules.service_catalog.domain.repositories.i_service_type_repo import (
    IServiceTypeRepository,
)
from app.shared.domain.exceptions.exceptions import EntityAlreadyExists, RepositoryError
from app.shared.domain.value_objects.money import Money
from app.shared.infra.database.error_handler import handle_db_error
from interfaces.i_logger import ILogger

Row = asyncpg.Record | Mapping[str, Any]

SELECT_ALL_COLUMNS = """
id,
name,
description AS desc,
price,
is_active,
is_primary,
created_at,
updated_at,
deleted_at
""".strip()


def _mapper(row: Row) -> ServiceType:
    if row is None:
        raise RepositoryError("Service type row is None")

    return ServiceType(
        id=row["id"],
        name=row["name"],
        desc=row["desc"],
        price=Money(row["price"]),
        is_active=row["is_active"],
        is_primary=row["is_primary"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row["deleted_at"],
    )


class AsyncPgServiceTypeRepository(IServiceTypeRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def get_by_id(self, service_type_id: int) -> ServiceType | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM service_catalog.service_types
                WHERE id = $1
                  AND deleted_at IS NULL;
                """,
                service_type_id,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"service_type_id": service_type_id},
            operation_name="fetch service type by id",
        )

    async def get_by_name(self, service_name: str) -> ServiceType | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM service_catalog.service_types
                WHERE name = $1
                  AND deleted_at IS NULL;
                """,
                service_name,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"service_name": service_name},
            operation_name="fetch service type by name",
        )

    async def list(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[ServiceType], int]:
        async def _fetch():
            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM service_catalog.service_types
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC, id DESC
                LIMIT $1 OFFSET $2;
                """,
                limit,
                offset,
            )
            total = await self.db.fetchval(
                """
                SELECT COUNT(*)
                FROM service_catalog.service_types
                WHERE deleted_at IS NULL;
                """
            )
            return [_mapper(row) for row in rows], int(total or 0)

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"limit": limit, "offset": offset},
            operation_name="list service types",
        )

    async def add(self, service_type: ServiceType) -> ServiceType:
        async def _create():
            try:
                row = await self.db.fetchrow(
                    f"""
                    INSERT INTO service_catalog.service_types (
                        name,
                        description,
                        price,
                        is_active,
                        is_primary
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING {SELECT_ALL_COLUMNS};
                    """,
                    service_type.name,
                    service_type.desc,
                    service_type.price.amount,
                    service_type.is_active,
                    service_type.is_primary,
                )
            except asyncpg.UniqueViolationError as exc:
                raise EntityAlreadyExists("ServiceType", service_type.name) from exc

            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={"service_type_name": service_type.name},
            operation_name="create service type",
        )

    async def save(self, service_type: ServiceType) -> ServiceType:
        async def _update():
            row = await self.db.fetchrow(
                f"""
                UPDATE service_catalog.service_types
                SET name = $1,
                    description = $2,
                    price = $3,
                    is_active = $4,
                    is_primary = $5,
                    updated_at = NOW()
                WHERE id = $6
                  AND deleted_at IS NULL
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                service_type.name,
                service_type.desc,
                service_type.price.amount,
                service_type.is_active,
                service_type.is_primary,
                service_type.id,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_update,
            logger=self.logger,
            context={"service_type_id": service_type.id},
            operation_name="update service type",
        )

    async def delete(self, service_type: ServiceType) -> ServiceType:
        async def _delete():
            row = await self.db.fetchrow(
                f"""
                UPDATE service_catalog.service_types
                SET is_active = $1,
                    deleted_at = $2,
                    updated_at = NOW()
                WHERE id = $3
                  AND deleted_at IS NULL
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                service_type.is_active,
                service_type.deleted_at,
                service_type.id,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_delete,
            logger=self.logger,
            context={"service_type_id": service_type.id},
            operation_name="soft delete service type",
        )
