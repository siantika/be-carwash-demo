import asyncpg
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager

from app.shared.config.settings import settings


async def get_db(request: Request):
    async with request.app.state.db_pool.acquire() as conn:
        yield conn


def get_db_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.db_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    dsn = getattr(settings, "DATABASE_URL", None)

    try:
        if dsn:
            app.state.db_pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=1,
                max_size=10,
                command_timeout=60,
                max_inactive_connection_lifetime=300,
            )
        else:
            app.state.db_pool = await asyncpg.create_pool(
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                host=settings.DB_HOST,
                port=int(settings.DB_PORT),
                min_size=1,
                max_size=10,
                command_timeout=60,
                max_inactive_connection_lifetime=300,
            )

        yield
    finally:
        pool = getattr(app.state, "db_pool", None)
        if pool:
            await pool.close()
