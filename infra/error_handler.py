import asyncio
from typing import Any, Callable, Dict

from domain.exceptions import RepositoryError
from interfaces.i_logger import ILogger


async def handle_db_error(
    operation: Callable[[], asyncio.Future[Any]],
    logger: ILogger,
    context: Dict[str, Any] = {} ,
    operation_name: str = "database operation"
) -> Any:
    try:
        return await operation()
    except Exception as error:
        if _is_infra_error(error):
            logger.error(
                f"Infra error in {operation_name}",
                error_type=type(error).__name__,
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