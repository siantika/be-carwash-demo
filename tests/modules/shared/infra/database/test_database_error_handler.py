import pytest

from app.shared.domain.exceptions.exceptions import RepositoryError
from app.shared.infra.database.error_handler import handle_db_error


class FakeAsyncPgError(Exception):
    pass


FakeAsyncPgError.__module__ = "asyncpg.exceptions"


class FakeLogger:
    def __init__(self):
        self.errors = []

    def error(self, event: str, **kwargs):
        self.errors.append((event, kwargs))


@pytest.mark.anyio
async def test_handle_db_error_classifies_asyncpg_errors_as_infra_errors():
    async def operation():
        raise FakeAsyncPgError("duplicate key")

    logger = FakeLogger()

    with pytest.raises(RepositoryError, match="Failed to insert account"):
        await handle_db_error(
            operation,
            logger,
            context={"account_id": 42},
            operation_name="insert account",
        )

    assert logger.errors == [
        (
            "Infra error in insert account",
            {
                "error_type": "FakeAsyncPgError",
                "error_message": "duplicate key",
                "exc_info": True,
                "account_id": 42,
            },
        )
    ]
