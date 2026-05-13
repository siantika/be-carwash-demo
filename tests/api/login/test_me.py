import httpx
import pytest

from app.api.dependencies.shared import get_current_user
from app.main import app
from app.modules.identity.application.dto.auth_context_dto import AuthContextDto


async def _current_user_override() -> AuthContextDto:
    return AuthContextDto(
        user_id=1,
        username="cashier_01",
        role="CASHIER",
    )


@pytest.mark.anyio
async def test_me_returns_current_user_context() -> None:
    app.dependency_overrides[get_current_user] = _current_user_override

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "user_id": 1,
            "username": "cashier_01",
            "role": "CASHIER",
        },
        "metadata": None,
    }
