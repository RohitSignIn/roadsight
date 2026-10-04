import base64
import asyncio
import shutil
from uuid import UUID, uuid4
from backend.app.jobs.bundle import BundleWriter
from backend.app.jobs.response import LeasedFileResponse
from backend.app.errors import JobNotFoundError, UploadTooLargeError

from fastapi import APIRouter, File, Form, Request, UploadFile

from backend.app.errors import ModelUnavailableError
from backend.app.media.image import ImageProcessor
from backend.app.schemas import ImageDetectionResponse


router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/detect", response_model=ImageDetectionResponse)
async def detect_image(
    request: Request,
    file: UploadFile = File(...),
    confidence: float = Form(0.25, ge=0.0, le=1.0),
) -> ImageDetectionResponse:
    runtime = request.app.state.runtime
    if runtime is None:
        raise ModelUnavailableError("Vehicle detection model is unavailable.")
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise UploadTooLargeError("Images must be 10 MB or smaller.")
    result = await asyncio.to_thread(ImageProcessor(runtime).process, data, confidence)
    storage = request.app.state.job_storage
    job_id = uuid4()
    paths = storage.create(job_id)
    try:
        with storage.lease(job_id):
            image = paths.output_dir / "processed_image.jpg"
            image.write_bytes(result.annotated_jpeg)
            await asyncio.to_thread(BundleWriter().write_image_result, paths=paths,
                annotated_media=image, records=result.vehicles,
                metadata={"source":"image","model":runtime.model_name,"device":runtime.device})
            storage.touch(job_id)
    except Exception:
        shutil.rmtree(paths.root, ignore_errors=True)
        raise
    return ImageDetectionResponse(
        download_url=f"/api/images/{job_id}/download",
        annotated_image_base64=base64.b64encode(result.annotated_jpeg).decode("ascii"),
        vehicles=result.vehicles,
    )


@router.get("/{job_id}/download")
async def download_image(request: Request, job_id: UUID):
    storage = request.app.state.job_storage
    path = storage.paths(job_id).root / "result.zip"
    if not path.is_file():
        raise JobNotFoundError("This image result was not found or has expired.")
    return LeasedFileResponse(storage, job_id, path, filename="vehicle-image-results.zip")
