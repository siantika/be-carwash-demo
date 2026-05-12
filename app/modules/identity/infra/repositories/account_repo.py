from typing import Any

import asyncpg

from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.exceptions.exceptions import EntityAlreadyExists, RepositoryError
from app.shared.infra.database.error_handler import handle_db_error
from interfaces.i_logger import ILogger

SELECT_ALL_COLUMNS = """
id,
username,
email,
role,
password_hash,
is_active,
failed_login_attempts,
locked_until,
last_login_at,
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
        email=Email(values["email"]),
        role=_validate_role(values["role"]),
        password_hash=values["password_hash"],
        is_active=values["is_active"],
        failed_login_attempts=values["failed_login_attempts"],
        locked_until=values["locked_until"],
        last_login_at=values["last_login_at"],
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
                FROM identity.accounts
                WHERE id = $1
                AND deleted_at IS NULL;
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
                FROM identity.accounts
                WHERE username = $1
                AND deleted_at IS NULL;
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

    async def find_all_filtered(
        self,
        role: RoleCode | None,
        is_active: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Account], int]:
        async def _fetch():
            conditions = ["deleted_at IS NULL"]
            params: list[Any] = []

            if role is not None:
                params.append(role.value)
                conditions.append(f"role = ${len(params)}")

            if is_active is not None:
                params.append(is_active)
                conditions.append(f"is_active = ${len(params)}")

            where_clause = " AND ".join(conditions)
            limit_param = len(params) + 1
            offset_param = len(params) + 2

            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM identity.accounts
                WHERE {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT ${limit_param} OFFSET ${offset_param};
                """,
                *params,
                limit,
                offset,
            )
            total = await self.db.fetchval(
                f"""
                SELECT COUNT(*)
                FROM identity.accounts
                WHERE {where_clause};
                """,
                *params,
            )
            return [_mapper(row) for row in rows], int(total or 0)

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={
                "role": role.value if role is not None else None,
                "is_active": is_active,
                "limit": limit,
                "offset": offset,
            },
            operation_name="list identity.accounts",
        )

    async def create(self, account: Account) -> Account:
        async def _create():
            try:
                row = await self.db.fetchrow(
                    f"""
                    INSERT INTO identity.accounts (
                        username,
                        email,
                        password_hash,
                        role,
                        is_active,
                        failed_login_attempts,
                        locked_until,
                        last_login_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING {SELECT_ALL_COLUMNS};
                    """,
                    account.username.value,
                    account.email.value,
                    account.password_hash,
                    account.role.value,
                    account.is_active,
                    account.failed_login_attempts,
                    account.locked_until,
                    account.last_login_at,
                )
            except asyncpg.UniqueViolationError as exc:
                raise EntityAlreadyExists("Account", account.username.value) from exc
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
                UPDATE identity.accounts
                SET username = $1,
                    email = $2,
                    password_hash = $3,
                    role = $4,
                    is_active = $5,
                    failed_login_attempts = $6,
                    locked_until = $7,
                    last_login_at = $8,
                    updated_at = NOW()
                WHERE id = $9
                  AND deleted_at IS NULL
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                account.username.value,
                account.email.value,
                account.password_hash,
                account.role.value,
                account.is_active,
                account.failed_login_attempts,
                account.locked_until,
                account.last_login_at,
                account.id,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_save,
            logger=self.logger,
            context={"account_id": account.id},
            operation_name="save account",
        )

    async def delete(self, account_id: int) -> int:
        async def _delete():
            row = await self.db.fetchrow(
                """
                UPDATE identity.accounts
                SET deleted_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1 AND deleted_at IS NULL
                RETURNING id;
                """,
                account_id,
            )
            if row is None:
                raise RepositoryError("Account not found or already deleted")
            return row["id"]

        return await handle_db_error(
            operation=_delete,
            logger=self.logger,
            context={"account_id": account_id},
            operation_name="delete account",
        )
