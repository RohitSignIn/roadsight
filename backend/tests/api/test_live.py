import base64
import json
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.schemas import Box, Detection


class Runtime:
    device = "cpu"
    model_name = "best.pt"
    def detect(self, frame, confidence):
        return [Detection(class_id=0,class_name="car",confidence=.9,box=Box(x1=2,y1=2,x2=20,y2=20))]


def encoded_frame() -> str:
    ok, data = cv2.imencode(".jpg", np.zeros((24, 32, 3), dtype=np.uint8))
    assert ok
    return base64.b64encode(data).decode()


def test_live_socket_returns_sequence_tagged_detection_and_isolates_sessions(tmp_path: Path) -> None:
    app=create_app(settings=Settings.load(tmp_path),runtime_loader=lambda _:Runtime())
    with TestClient(app) as client:
        for _ in range(2):
            with client.websocket_connect("/api/live") as socket:
                socket.send_json({"sequence":7,"image":encoded_frame(),"confidence":.25})
                result=socket.receive_json()
                assert result["sequence"]==7
                assert result["total_unique"]==1
                assert result["vehicles"][0]["vehicle_id"]==1


def test_live_socket_reports_malformed_frames_without_closing(tmp_path: Path) -> None:
    app=create_app(settings=Settings.load(tmp_path),runtime_loader=lambda _:Runtime())
    with TestClient(app) as client, client.websocket_connect("/api/live") as socket:
        socket.send_text(json.dumps({"sequence":1,"image":"not-base64"}))
        assert socket.receive_json()=={"sequence":1,"error":{"code":"invalid_media","message":"Invalid camera frame."}}
        socket.send_json({"sequence":2,"image":encoded_frame()})
        assert socket.receive_json()["sequence"]==2
