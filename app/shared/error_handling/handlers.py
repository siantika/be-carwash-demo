import logging

from fastapi import FastAPI, Request, status
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
    InvalidTokenError,
    PermissionDeniedError,
    RepositoryError,
)
from app.shared.response import BaseErrorResponse, ErrorResponse

# Setup logger for error handler
logger = logging.getLogger(__name__)

EXCEPTION_STATUS_MAP = {
    InvalidPasswordError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    InactiveUserError: status.HTTP_403_FORBIDDEN,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
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


def _dump_error_response(response: BaseErrorResponse) -> dict:
    return response.model_dump(exclude_none=True)


def _format_validation_location(location: tuple) -> str:
    return ".".join(str(part) for part in location if part != "body")


def _build_validation_details(errors: list[dict]) -> dict:
    fields: dict[str, list[dict[str, str]]] = {}

    for error in errors:
        field = _format_validation_location(tuple(error.get("loc", ()))) or "body"
        fields.setdefault(field, []).append(
            {
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            }
        )

    return {"fields": fields}


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError):
        status_code = _resolve_status_code(exc)
        return JSONResponse(
            status_code=status_code,
            content=_dump_error_response(BaseErrorResponse(
                error=ErrorResponse(
                    code=exc.__class__.__name__,
                    message=str(exc),
                )
            )),
        )

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "RouteNotFound"
            message = "Route not found"
        else:
            code = exc.__class__.__name__
            message = str(exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
            content=_dump_error_response(BaseErrorResponse(
                error=ErrorResponse(
                    code=code,
                    message=message,
                )
            )),
        )

    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
        # Only show the error field without full error message
        errors = exc.errors()
        error_fields = [
            _format_validation_location(tuple(err.get("loc", ())))
            for err in errors
            if err.get("loc")
        ]
        error_fields = [field for field in error_fields if field]
        message = f"Data is not valid on fields: {', '.join(sorted(set(error_fields)))}" if error_fields else "Data tidak valid."

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_dump_error_response(BaseErrorResponse(
                error=ErrorResponse(
                    code="RequestValidationError",
                    message=message,
                    details=_build_validation_details(errors),
                )
            ))
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
            content=_dump_error_response(BaseErrorResponse(
                error=ErrorResponse(
                    code="InternalServerError",
                    message="Internal server error",
                )
            )),
        )
