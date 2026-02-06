import httpx
import pytest

from main import app


@pytest.mark.anyio
async def test_health_async():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/health")
        
    assert r.status_code == 200
