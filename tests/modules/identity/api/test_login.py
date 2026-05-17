import pytest

from app.main import app
from app.modules.identity.api.dependencies import get_login_usecase


class FakeLoginUseCase:
    async def execute(self, username: str, password: str):
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token-abcdefghijklmnopqrstuvwxyz012345",
            "token_type": "bearer",
        }


def _login_usecase_override() -> FakeLoginUseCase:
    return FakeLoginUseCase()


@pytest.mark.anyio
async def test_success_login(client):
    app.dependency_overrides[get_login_usecase] = _login_usecase_override

    try:
        r = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin01", "password": "admin1234"},
        )
    finally:
        app.dependency_overrides.pop(get_login_usecase, None)

    assert r.status_code == 200
    assert r.json() == {
        "data": {
            "access_token": "access-token",
            "refresh_token": "refresh-token-abcdefghijklmnopqrstuvwxyz012345",
            "token_type": "bearer",
        },
        "metadata": None,
    }
