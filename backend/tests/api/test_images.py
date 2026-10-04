import base64
from pathlib import Path

import cv2
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.schemas import Box, Detection


async def post_image(app, payload: bytes, content_type: str = "image/jpeg"):
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post(
                "/api/images/detect",
                files={"file": ("vehicle.jpg", payload, content_type)},
                data={"confidence": "0.25"},
            )


@pytest.mark.asyncio
async def test_image_endpoint_returns_annotated_image_and_vehicle_metadata(tmp_path: Path) -> None:
    frame = np.zeros((32, 48, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".jpg", frame)
    assert success

    class FakeRuntime:
        device = "cpu"
        model_name = "best.pt"

        def detect(self, frame, confidence):
            return [
                Detection(
                    class_id=3,
                    class_name="car",
                    confidence=0.8,
                    box=Box(x1=3, y1=4, x2=30, y2=25),
                )
            ]

    app = create_app(settings=Settings.load(tmp_path), runtime_loader=lambda _: FakeRuntime())
    response = await post_image(app, encoded.tobytes())

    assert response.status_code == 200
    body = response.json()
    assert base64.b64decode(body["annotated_image_base64"]).startswith(b"\xff\xd8")
    assert body["vehicles"] == [
        {
            "vehicle_id": 1,
            "vehicle_type": "car",
            "color": "black",
            "first_seen": 0.0,
            "last_seen": 0.0,
            "duration_seconds": 0.0,
            "direction": "stationary",
            "average_confidence": 0.8,
            "maximum_confidence": 0.8,
            "relative_size": pytest.approx(0.369140625),
        }
    ]


@pytest.mark.asyncio
async def test_image_endpoint_rejects_malformed_content(tmp_path: Path) -> None:
    runtime = type("Runtime", (), {"device": "cpu", "model_name": "best.pt"})()
    app = create_app(settings=Settings.load(tmp_path), runtime_loader=lambda _: runtime)

    response = await post_image(app, b"not an image")

    assert response.status_code == 415
    assert response.json() == {
        "error": {"code": "invalid_media", "message": "The uploaded file is not a valid image."}
    }


@pytest.mark.asyncio
async def test_image_endpoint_returns_503_when_model_is_unavailable(tmp_path: Path) -> None:
    app = create_app(
        settings=Settings.load(tmp_path),
        runtime_loader=lambda _: (_ for _ in ()).throw(RuntimeError("load failed")),
    )

    response = await post_image(app, b"anything")

    assert response.status_code == 503
    assert response.json() == {
        "error": {"code": "model_unavailable", "message": "Vehicle detection model is unavailable."}
    }
