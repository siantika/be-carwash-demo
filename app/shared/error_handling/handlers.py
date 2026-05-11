import logging

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.domain.exceptions.exceptions import (
    AppError,
    BusinessRuleViolation,
    EntityAlreadyExists,
    EntityNotFound,
    InactiveUserError,
    InvalidPasswordError,
    RepositoryError,
)
from app.shared.response import BaseErrorResponse, ErrorResponse

# Setup logger for error handler
logger = logging.getLogger(__name__)

EXCEPTION_STATUS_MAP = {
    InvalidPasswordError: status.HTTP_401_UNAUTHORIZED,
    InactiveUserError: status.HTTP_403_FORBIDDEN,
    EntityNotFound: status.HTTP_404_NOT_FOUND,
    EntityAlreadyExists: status.HTTP_409_CONFLICT,
    BusinessRuleViolation: status.HTTP_400_BAD_REQUEST,
    RepositoryError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    AppError: status.HTTP_400_BAD_REQUEST,
}


def _resolve_status_code(exc: AppError) -> int:
    for exc_type, code in EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return code
    return status.HTTP_400_BAD_REQUEST


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError):
        status_code = _resolve_status_code(exc)
        return JSONResponse(
            status_code=status_code,
            content=BaseErrorResponse(
                error=ErrorResponse(
                    code=exc.__class__.__name__,
                    message=str(exc),
                )
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
        # Only show the error field without full error message
        error_fields = [err["loc"][-1] for err in exc.errors() if "loc" in err]
        message = f"Data is not valid on fields: {', '.join(set(error_fields))}" if error_fields else "Data tidak valid."

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=BaseErrorResponse(
                error=ErrorResponse(
                    code="RequestValidationError",
                    message=message,
                )
            ).model_dump()
        )
        
    # Fallback for unexpected exception
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Exclude these exceptions (explicit system exit by the programmer)
        if isinstance(exc, (SystemExit, KeyboardInterrupt)):
            raise

        logger.error("Unhandled exception", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=BaseErrorResponse(
                error=ErrorResponse(
                    code="InternalServerError",
                    message="Internal server error",
                )
            ).model_dump(),
        )
