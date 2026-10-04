from pathlib import Path
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.config import Settings
from backend.app.errors import ModelUnavailableError
from backend.app.main import create_app


@pytest.mark.asyncio
async def test_health_reports_loaded_model_and_device(tmp_path: Path) -> None:
    settings = Settings.load(tmp_path)
    runtime = SimpleNamespace(device="cpu", model_name="best.pt")
    app = create_app(settings=settings, runtime_loader=lambda _: runtime)

    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "ready": True,
        "device": "cpu",
        "model": "best.pt",
        "message": None,
    }


@pytest.mark.asyncio
async def test_health_reports_safe_message_when_model_load_fails(tmp_path: Path) -> None:
    settings = Settings.load(tmp_path)

    def fail_to_load(_: Settings):
        raise ModelUnavailableError("private filesystem details")

    app = create_app(settings=settings, runtime_loader=fail_to_load)

    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "ready": False,
        "device": None,
        "model": "best.pt",
        "message": "Vehicle detection model is unavailable.",
    }
    assert app.state.runtime is None
