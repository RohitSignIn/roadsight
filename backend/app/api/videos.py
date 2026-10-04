from __future__ import annotations

import tempfile
import asyncio
from pathlib import Path
from uuid import UUID

import cv2
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from backend.app.jobs.response import LeasedFileResponse

from backend.app.errors import InvalidMediaError, JobNotFoundError, ModelUnavailableError, UploadTooLargeError


router = APIRouter(prefix="/api/videos", tags=["videos"])
SUPPORTED_SUFFIXES = {".mp4", ".webm", ".avi", ".mov"}


def _snapshot(manager, job_id: UUID):
    if manager is None:
        raise ModelUnavailableError("Vehicle detection model is unavailable.")
    try:
        return manager.get(job_id)
    except KeyError as exc:
        raise JobNotFoundError("Video job was not found or has expired.") from exc


@router.post("")
async def create_video_job(
    request: Request,
    file: UploadFile = File(...),
    confidence: float = Form(0.25, ge=0.0, le=1.0),
):
    if request.app.state.runtime is None:
        raise ModelUnavailableError("Vehicle detection model is unavailable.")
    limit = request.app.state.settings.max_video_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise UploadTooLargeError("Video files must be 10 MB or smaller.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES or not await asyncio.to_thread(_is_decodable, data, suffix):
        raise InvalidMediaError("The uploaded file is not a valid supported video.")
    return await request.app.state.job_manager.submit(data, suffix, confidence)


@router.get("/{job_id}")
async def get_video_job(request: Request, job_id: UUID):
    return _snapshot(request.app.state.job_manager, job_id)


@router.delete("/{job_id}")
async def cancel_video_job(request: Request, job_id: UUID):
    _snapshot(request.app.state.job_manager, job_id)
    return await request.app.state.job_manager.cancel(job_id)


@router.get("/{job_id}/download")
async def download_video_job(request: Request, job_id: UUID):
    snapshot = _snapshot(request.app.state.job_manager, job_id)
    if not snapshot.download_ready:
        raise JobNotFoundError("The video result is not available for download.")
    storage = request.app.state.job_storage
    return LeasedFileResponse(storage, job_id, storage.paths(job_id).root / "result.zip",
                              filename=f"vehicle-detection-{job_id}.zip")


@router.get("/{job_id}/preview")
async def preview_video(request: Request, job_id: UUID):
    snapshot = _snapshot(request.app.state.job_manager, job_id)
    if not snapshot.download_ready:
        raise JobNotFoundError("The video result is unavailable or expired.")
    storage = request.app.state.job_storage
    return LeasedFileResponse(storage, job_id, storage.paths(job_id).output_dir / "processed_video.mp4",
                              media_type="video/mp4")


def _is_decodable(data: bytes, suffix: str) -> bool:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(data)
            temp_path = Path(handle.name)
        capture = cv2.VideoCapture(str(temp_path))
        ok, frame = capture.read()
        capture.release()
        return bool(ok and frame is not None and frame.size)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
