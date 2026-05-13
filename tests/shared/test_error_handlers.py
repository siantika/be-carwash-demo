import httpx
import pytest
from fastapi import Depends, FastAPI, HTTPException, status

from app.api.dependencies.shared import get_current_user
from app.shared.error_handling.handlers import register_exception_handlers


@pytest.mark.anyio
async def test_http_exception_uses_base_error_response():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/protected")
    async def protected():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/protected")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "error": {
            "code": "HTTPException",
            "message": "Invalid token",
        }
    }


@pytest.mark.anyio
async def test_auth_dependency_exception_uses_base_error_response():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/me")
    async def me(user=Depends(get_current_user)):
        return user

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "error": {
            "code": "NotAuthenticatedError",
            "message": "Not authenticated",
        }
    }
