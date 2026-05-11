from typing import Any

import asyncpg

from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.exceptions.exceptions import RepositoryError
from app.shared.infra.database.error_handler import handle_db_error
from interfaces.i_logger import ILogger

SELECT_ALL_COLUMNS = """
id,
username,
role,
password_hash,
is_active,
created_at,
updated_at
""".strip()


def _validate_role(value: str) -> RoleCode:
    try:
        return RoleCode(value)
    except ValueError as exc:
        raise RepositoryError(f"Invalid account role from DB: {value}") from exc


def _mapper(row: asyncpg.Record) -> Account:
    if row is None:
        raise RepositoryError("Account row is None")

    values: dict[str, Any] = dict(row)
    username = Username(values["username"])

    return Account(
        id=values["id"],
        username=username,
        email=Email(values.get("email") or f"{username.value}@local.invalid"),
        role=_validate_role(values["role"]),
        password_hash=values["password_hash"],
        is_active=values["is_active"],
        created_at=values["created_at"],
        updated_at=values["updated_at"],
    )


class AsyncPgAccountRepository(IAccountRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def find_by_id(self, account_id: int) -> Account | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM users
                WHERE id = $1;
                """,
                account_id,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"account_id": account_id},
            operation_name="fetch account by id",
        )

    async def find_by_username(self, username: Username) -> Account | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM users
                WHERE username = $1;
                """,
                username.value,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"username": username.value},
            operation_name="fetch account by username",
        )

    async def find_all(self) -> list[Account]:
        async def _fetch():
            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM users
                ORDER BY created_at DESC, id DESC;
                """
            )
            return [_mapper(row) for row in rows]

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={},
            operation_name="list accounts",
        )

    async def find_all_by_role(self, role: RoleCode) -> list[Account]:
        async def _fetch():
            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM users
                WHERE role = $1
                ORDER BY created_at DESC, id DESC;
                """,
                role.value,
            )
            return [_mapper(row) for row in rows]

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"role": role.value},
            operation_name="list accounts by role",
        )

    async def find_all_by_status(self, is_active: bool) -> list[Account]:
        async def _fetch():
            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM users
                WHERE is_active = $1
                ORDER BY created_at DESC, id DESC;
                """,
                is_active,
            )
            return [_mapper(row) for row in rows]

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"is_active": is_active},
            operation_name="list accounts by status",
        )

    async def create(self, account: Account) -> Account:
        async def _create():
            row = await self.db.fetchrow(
                f"""
                INSERT INTO users (
                    username,
                    password_hash,
                    role,
                    is_active
                )
                VALUES ($1, $2, $3, $4)
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                account.username.value,
                account.password_hash,
                account.role.value,
                account.is_active,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={"username": account.username.value},
            operation_name="create account",
        )

    async def save(self, account: Account) -> Account:
        async def _save():
            row = await self.db.fetchrow(
                f"""
                UPDATE users
                SET username = $1,
                    password_hash = $2,
                    role = $3,
                    is_active = $4,
                    updated_at = NOW()
                WHERE id = $5
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                account.username.value,
                account.password_hash,
                account.role.value,
                account.is_active,
                account.id,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_save,
            logger=self.logger,
            context={"account_id": account.id},
            operation_name="save account",
        )

    async def delete(self, account_id: int) -> None:
        async def _delete():
            await self.db.execute(
                """
                DELETE FROM users
                WHERE id = $1;
                """,
                account_id,
            )

        await handle_db_error(
            operation=_delete,
            logger=self.logger,
            context={"account_id": account_id},
            operation_name="delete account",
        )
