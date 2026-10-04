import asyncio
import io
import threading
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from zipfile import ZipFile

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.jobs.storage import JobStorage
from backend.app.jobs.response import LeasedFileResponse
from backend.app.main import create_app
from backend.tests.api.test_live import Runtime, encoded_frame


def test_nested_download_leases_remain_protected(tmp_path):
    storage=JobStorage(tmp_path,ttl=timedelta(seconds=1))
    job=uuid4()
    storage.create(job)
    future=datetime.now(UTC)+timedelta(hours=1)
    with storage.lease(job):
        with storage.lease(job):
            assert storage.cleanup_expired(future)==[]
        assert storage.cleanup_expired(future)==[]
    assert storage.cleanup_expired(future)==[job]


@pytest.mark.asyncio
async def test_lease_covers_actual_file_send(tmp_path):
    storage=JobStorage(tmp_path,ttl=timedelta(seconds=1))
    job=uuid4(); paths=storage.create(job)
    file=paths.root/"result.zip";file.write_bytes(b"test")
    response=LeasedFileResponse(storage,job,file)
    async def send(message):
        assert storage.cleanup_expired(datetime.now(UTC)+timedelta(hours=1))==[]
    async def receive():
        return {"type":"http.request"}
    await response({"type":"http","method":"GET","headers":[]},receive,send)
    assert storage.cleanup_expired(datetime.now(UTC)+timedelta(hours=1))==[job]


def test_image_bundle_contains_image_and_history(tmp_path):
    app=create_app(settings=Settings.load(tmp_path),runtime_loader=lambda _:Runtime())
    _, image=cv2.imencode(".jpg",np.zeros((32,32,3),dtype=np.uint8))
    with TestClient(app) as client:
        response=client.post("/api/images/detect",files={"file":("car.jpg",image.tobytes(),"image/jpeg")})
        assert response.status_code==200
        result=client.get(response.json()["download_url"])
        with ZipFile(io.BytesIO(result.content)) as archive:
            assert {"processed_image.jpg","vehicle_history.csv","vehicle_history.json","summary.json"}<=set(archive.namelist())


def test_live_does_not_block_http_and_keeps_latest_pending_frame(tmp_path):
    entered,release=threading.Event(),threading.Event()
    class Slow(Runtime):
        def detect(self,frame,confidence):
            entered.set()
            assert release.wait(3)
            return super().detect(frame,confidence)
    app=create_app(settings=Settings.load(tmp_path),runtime_loader=lambda _:Slow())
    with TestClient(app) as client, client.websocket_connect("/api/live") as socket:
        try:
            socket.send_json({"sequence":1,"image":encoded_frame()})
            assert entered.wait(2)
            # A blocked event loop cannot serve this health request.
            assert client.get("/api/health").status_code==200
            for sequence in range(2,8):
                socket.send_json({"sequence":sequence,"image":encoded_frame()})
            # Receiving an invalid message ACK proves the receiver consumed preceding frames.
            socket.send_json({"sequence":8,"image":"invalid"})
            assert socket.receive_json()["error"]["code"]=="invalid_media"
        finally:
            release.set()
        assert socket.receive_json()["sequence"]==7


def test_video_preview_and_bundle_include_crops(tmp_path):
    path=tmp_path/"input.mp4"
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*"mp4v"),10,(32,24))
    for _ in range(3): writer.write(np.zeros((24,32,3),dtype=np.uint8))
    writer.release()
    app=create_app(settings=Settings.load(tmp_path),runtime_loader=lambda _:Runtime())
    with TestClient(app) as client:
        response=client.post("/api/videos",files={"file":("input.mp4",path.read_bytes(),"video/mp4")})
        assert response.status_code==200
        job_id=response.json()["id"]
        import time
        for _ in range(200):
            body=client.get(f"/api/videos/{job_id}").json()
            if body["status"] not in ("queued","processing"):break
            time.sleep(.02)
        assert body["status"]=="completed",body
        assert len(body["vehicles"])==1
        assert client.get(body["preview_url"]).headers["content-type"]=="video/mp4"
        with ZipFile(io.BytesIO(client.get(f"/api/videos/{job_id}/download").content)) as archive:
            assert "vehicle_crops/vehicle_1.jpg" in archive.namelist()
