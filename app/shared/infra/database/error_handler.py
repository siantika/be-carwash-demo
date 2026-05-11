import asyncio
from typing import Any, Callable, Dict

import asyncpg

from app.shared.domain.exceptions.exceptions import AppError, RepositoryError
from interfaces.i_logger import ILogger


async def handle_db_error(
    operation: Callable[[], asyncio.Future[Any]],
    logger: ILogger,
    context: Dict[str, Any] = {} ,
    operation_name: str = "database operation"
) -> Any:
    try:
        return await operation()
    except AppError:
        raise
    except Exception as error:
        if _is_infra_error(error):
            error_details = _get_infra_error_details(error)
            logger.error(
                f"Infra error in {operation_name}",
                error_type=type(error).__name__,
                error_message=str(error),
                exc_info=True,
                **error_details,
                **context
            )
            raise RepositoryError(f"Failed to {operation_name}") from error
        else:
            logger.error(
                f"Unexpected error in {operation_name}",
                error_type=type(error).__name__,
                exc_info=True,
                **context
            )
            raise RepositoryError(f"Unexpected failure in {operation_name}") from error

def _is_infra_error(error: Exception) -> bool:
    """Correlated to specific database tech (asyncpg for this case)"""
    infra_modules = (
        "asyncpg.exceptions"
    )
    return any(type(error).__module__.startswith(m) for m in infra_modules)


def _get_infra_error_details(error: Exception) -> dict[str, Any]:
    if not isinstance(error, asyncpg.PostgresError):
        return {}

    return {
        "sqlstate": getattr(error, "sqlstate", None),
        "detail": getattr(error, "detail", None),
        "constraint_name": getattr(error, "constraint_name", None),
        "schema_name": getattr(error, "schema_name", None),
        "table_name": getattr(error, "table_name", None),
        "column_name": getattr(error, "column_name", None),
    }
