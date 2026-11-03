"""Browser requests must match origins normalized by Pydantic URL parsing."""
import runpy
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import AnyHttpUrl

from app.core.config import settings


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setattr(settings, "BACKEND_CORS_ORIGINS", [
        AnyHttpUrl("http://localhost:5173"),
        AnyHttpUrl("http://127.0.0.1:5173"),
    ])
    # Construct the real app with explicit settings without reloading shared modules.
    app = runpy.run_path(str(Path(__file__).parents[1] / "app/main.py"))["app"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
async def test_patient_creation_preflight(client, origin):
    response = await client.options("/api/v1/patients/", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]


async def test_unauthenticated_response_is_readable_in_browser(client):
    response = await client.post("/api/v1/patients/", json={}, headers={
        "Origin": "http://localhost:5173",
    })
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["www-authenticate"] == "Bearer"


async def test_unlisted_origin_is_rejected(client):
    response = await client.options("/api/v1/patients/", headers={
        "Origin": "http://unlisted.example",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
