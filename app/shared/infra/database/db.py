from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from fastapi import FastAPI, Request

from app.shared.config.settings import settings

_pool: asyncpg.Pool | None = None


def _database_url() -> str:
    return (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    _pool = await asyncpg.create_pool(dsn=_database_url())
    app.state.db_pool = _pool
    try:
        yield
    finally:
        await _pool.close()
        _pool = None


def _get_global_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")

    return _pool


async def get_db_pool(request: Request) -> asyncpg.Pool:
    if hasattr(request.app.state, "db_pool"):
        return request.app.state.db_pool

    return _get_global_pool()


async def get_db(request: Request) -> AsyncIterator[asyncpg.Connection]:
    active_pool = (
        request.app.state.db_pool
        if hasattr(request.app.state, "db_pool")
        else _get_global_pool()
    )
    conn = await active_pool.acquire()
    try:
        yield conn
    finally:
        await active_pool.release(conn)
