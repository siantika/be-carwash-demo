from typing import List, Optional

import asyncpg

from app.modules.identity.domain.entities.user import User, UserRoleEnum
from app.shared.domain.exceptions.exceptions import RepositoryError
from domain.repositories.i_user_repo import IUserRepository
from infra.error_handler import handle_db_error
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


def _validate_user_role(value: str) -> UserRoleEnum:
    try:
        return UserRoleEnum(value)
    except ValueError as exc:
        raise RepositoryError(
            f"Invalid user role from DB: {value}"
        ) from exc


def _mapper(row: asyncpg.Record) -> User:
    if row is None:
        raise RepositoryError("User row is None")

    role = _validate_user_role(row["role"])
    
    return User(
        id=row["id"],
        username=row["username"],
        role=role.value,
        password_hash= row["password_hash"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncPgUserRepository(IUserRepository):
    def __init__(self, db:asyncpg.Connection, 
                 logger: ILogger):
        self.db = db
        self.logger = logger

    async def get_by_id(self, user_id: int) -> Optional[User]:
        async def _fetch():
            row = await self.db.fetchrow(f"""
                        SELECT {SELECT_ALL_COLUMNS}
                        FROM users
                        WHERE id = $1;
                    """,
                    user_id)
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"user_id": user_id},
            operation_name="fetch user by id"
        )

    async def get_by_username(self, username: str) -> Optional[User]:
        async def _fetch():
            row = await self.db.fetchrow(f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM users
                WHERE username = $1
            """, username)

            return _mapper(row) if row else None
        
        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"username": username},
            operation_name="fetch user by username"
        )

    async def list(self, limit:int, offset:int ) -> List[User]:
        async def _get():
            rows = await self.db.fetch(
                f"""
                    SELECT {SELECT_ALL_COLUMNS}
                    FROM users 
                    ORDER BY created_at DESC, id DESC
                    LIMIT $1 OFFSET $2;
                """,
                limit,
                offset
            )
            return [_mapper(user) for user in rows]
        
        return await handle_db_error(
            operation=_get,
            logger=self.logger,
            context={"limit": limit, "offset": offset},
            operation_name="list user"
        )

            
    async def add(self, user:User) -> User:
        async def _create():
            row = await self.db.fetchrow(f"""
                INSERT INTO users (username, password_hash, role, is_active)
                VALUES ($1, $2, $3, $4)
                RETURNING {SELECT_ALL_COLUMNS};
            """, user.username, user.password_hash, user.role, user.is_active)
            return _mapper(row) 
        
        return await handle_db_error(
            operation= _create,
            logger=self.logger,
            context={},
            operation_name="add user"
        )

    async def save (self, user:User) -> User:
        async def _update():
            row = await self.db.fetchrow(f"""
                UPDATE users
                SET username = $1, password_hash = $2, role = $3, is_active = $4
                WHERE id = $5
                RETURNING {SELECT_ALL_COLUMNS};
            """, user.username, user.password_hash, user.role, user.is_active, user.id)
            
            return _mapper(row)
        
        return await handle_db_error(
            operation= _update,
            logger=self.logger,
            context={"user_id": user.id},
            operation_name="save user"
        )
