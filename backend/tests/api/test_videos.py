import asyncio
from pathlib import Path

import cv2
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.config import Settings
from backend.app.main import create_app


class Runtime:
    device = "cpu"
    model_name = "best.pt"
    def detect(self, frame, confidence):
        return []


async def upload(app, data: bytes, name: str = "clip.mp4"):
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post("/api/videos", files={"file": (name, data, "video/mp4")})


@pytest.mark.asyncio
async def test_upload_rejects_more_than_ten_mb_without_retaining_job(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path, model_path=tmp_path / "best.pt")
    app = create_app(settings=settings, runtime_loader=lambda _: Runtime())
    response = await upload(app, b"x" * (settings.max_video_bytes + 1))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "upload_too_large"
    assert not (tmp_path / ".runtime" / "jobs").exists() or not any((tmp_path / ".runtime" / "jobs").iterdir())


@pytest.mark.asyncio
async def test_upload_rejects_fake_mp4(tmp_path: Path) -> None:
    app = create_app(settings=Settings.load(tmp_path), runtime_loader=lambda _: Runtime())
    response = await upload(app, b"fake mp4")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "invalid_media"


@pytest.mark.asyncio
async def test_exact_limit_is_not_rejected_as_too_large(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path, model_path=tmp_path / "best.pt", max_video_bytes=64)
    app = create_app(settings=settings, runtime_loader=lambda _: Runtime())
    response = await upload(app, b"x" * 64)
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "invalid_media"
