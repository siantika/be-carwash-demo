import asyncio
from dataclasses import dataclass
from decimal import Decimal

import asyncpg

from app.modules.identity.infra.security import hash_password
from app.shared.config.settings import settings


def _database_url() -> str:
    return (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


@dataclass(frozen=True)
class SeedAccount:
    username: str
    email: str
    password: str
    role: str
    is_active: bool = True


@dataclass(frozen=True)
class SeedDevice:
    device_code: str
    name: str
    location: str
    is_active: bool = True


@dataclass(frozen=True)
class SeedServiceType:
    name: str
    description: str
    price: Decimal
    is_primary: bool = False
    is_active: bool = True


ACCOUNTS = [
    SeedAccount("owner_demo", "owner@demo.local", "Owner123!", "OWNER"),
    SeedAccount("admin_demo", "admin@demo.local", "Admin123!", "ADMIN"),
    SeedAccount("cashier_demo", "cashier@demo.local", "Cashier123!", "CASHIER"),
]

DEVICES = [
    SeedDevice("BARRIER-GATE-001", "Barrier Gate Entry 1", "Entrance Lane A"),
    SeedDevice("BARRIER-GATE-002", "Barrier Gate Entry 2", "Entrance Lane B"),
]

SERVICE_TYPES = [
    SeedServiceType("Basic Wash", "Exterior wash only", Decimal("50000"), True),
    SeedServiceType("Premium Wash", "Exterior + interior cleaning", Decimal("85000")),
    SeedServiceType("Full Detailing", "Complete interior and exterior detailing", Decimal("150000")),
]


async def seed_accounts(conn: asyncpg.Connection) -> None:
    for account in ACCOUNTS:
        password_hash = hash_password(account.password)
        await conn.execute(
            """
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
            VALUES ($1, $2, $3, $4, $5, 0, NULL, NULL)
            ON CONFLICT (username)
            DO UPDATE SET
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                updated_at = NOW(),
                deleted_at = NULL;
            """,
            account.username,
            account.email,
            password_hash,
            account.role,
            account.is_active,
        )


async def seed_devices(conn: asyncpg.Connection) -> None:
    for device in DEVICES:
        await conn.execute(
            """
            INSERT INTO identity.devices (
                device_code,
                name,
                location,
                is_active,
                last_seen_at
            )
            VALUES ($1, $2, $3, $4, NULL)
            ON CONFLICT (device_code)
            DO UPDATE SET
                name = EXCLUDED.name,
                location = EXCLUDED.location,
                is_active = EXCLUDED.is_active,
                updated_at = NOW();
            """,
            device.device_code,
            device.name,
            device.location,
            device.is_active,
        )


async def seed_service_types(conn: asyncpg.Connection) -> None:
    for service_type in SERVICE_TYPES:
        await conn.execute(
            """
            INSERT INTO service_catalog.service_types (
                name,
                description,
                price,
                is_active,
                is_primary
            )
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (name)
            DO UPDATE SET
                description = EXCLUDED.description,
                price = EXCLUDED.price,
                is_active = EXCLUDED.is_active,
                is_primary = EXCLUDED.is_primary,
                updated_at = NOW(),
                deleted_at = NULL;
            """,
            service_type.name,
            service_type.description,
            service_type.price,
            service_type.is_active,
            service_type.is_primary,
        )


async def run() -> None:
    conn = await asyncpg.connect(dsn=_database_url())
    try:
        async with conn.transaction():
            await seed_accounts(conn)
            await seed_devices(conn)
            await seed_service_types(conn)
    finally:
        await conn.close()

    print("Seeding completed.")
    print("Demo credentials:")
    print("- owner_demo / Owner123!")
    print("- admin_demo / Admin123!")
    print("- cashier_demo / Cashier123!")
    print("Demo barrier gates: BARRIER-GATE-001, BARRIER-GATE-002")


if __name__ == "__main__":
    asyncio.run(run())
