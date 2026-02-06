import pytest


@pytest.mark.anyio
async def test_success_login(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin01", "password": "admin1234"},
    )
    assert r.status_code == 200
