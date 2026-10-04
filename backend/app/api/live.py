import asyncio
import base64
import json
import math
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.analytics.session import AnalyticsSession
from backend.app.media.validation import decode_image

router = APIRouter(tags=["live"])
MAX_FRAME_BYTES = 2 * 1024 * 1024


@router.websocket("/api/live")
async def live_detection(socket: WebSocket):
    await socket.accept()
    runtime = socket.app.state.runtime
    if runtime is None:
        await socket.send_json({"error": {"code": "model_unavailable", "message": "Vehicle detection model is unavailable."}})
        await socket.close(code=1011)
        return
    session = AnalyticsSession()
    pending = asyncio.Queue(maxsize=1)
    started = time.perf_counter()
    latest = -1

    async def receive():
        nonlocal latest
        while True:
            text = await socket.receive_text()
            sequence = None
            try:
                if len(text) > MAX_FRAME_BYTES * 2:
                    raise ValueError()
                payload = json.loads(text)
                sequence = payload["sequence"]
                confidence = float(payload.get("confidence", 0.25))
                if type(sequence) is not int or sequence < 0 or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                    raise ValueError()
                raw = base64.b64decode(payload["image"], validate=True)
                if len(raw) > MAX_FRAME_BYTES:
                    raise ValueError()
                if sequence <= latest:
                    continue
                latest = sequence
                if pending.full():
                    pending.get_nowait()
                pending.put_nowait((sequence, raw, confidence, time.perf_counter() - started))
            except (ValueError, KeyError, TypeError):
                await socket.send_json({"sequence": sequence, "error": {"code": "invalid_media", "message": "Invalid camera frame."}})

    def infer(raw, confidence, timestamp):
        frame = decode_image(raw)
        detections = runtime.detect(frame, confidence)
        session.observe(frame, detections, timestamp)
        records = session.history.records()
        return {
            "detections": [d.model_dump(mode="json") for d in detections],
            "vehicles": [r.model_dump(mode="json") for r in records],
            "total_unique": len(records), "width": frame.shape[1], "height": frame.shape[0],
        }

    async def process():
        while True:
            sequence, raw, confidence, timestamp = await pending.get()
            tick = time.perf_counter()
            try:
                result = await asyncio.to_thread(infer, raw, confidence, timestamp)
            except Exception:
                await socket.send_json({"sequence": sequence, "error": {"code": "invalid_media", "message": "Invalid camera frame."}})
                continue
            elapsed = max(time.perf_counter() - tick, 1e-6)
            if sequence < latest:
                continue
            await socket.send_json({**result, "sequence": sequence, "latency_ms": round(elapsed*1000, 1), "inference_fps": round(1/elapsed, 2)})

    tasks = [asyncio.create_task(receive()), asyncio.create_task(process())]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
