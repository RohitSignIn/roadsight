from __future__ import annotations
import asyncio
from contextlib import suppress

from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.health import router as health_router
from backend.app.api.images import router as images_router
from backend.app.api.live import router as live_router
from backend.app.api.videos import router as videos_router
from backend.app.config import Settings
from backend.app.detection.runtime import DetectionRuntime
from backend.app.errors import ApplicationError
from backend.app.jobs.manager import JobManager
from backend.app.jobs.storage import JobStorage
from backend.app.media.video import VideoProcessor


RuntimeLoader = Callable[[Settings], Any]


def create_app(
    *,
    settings: Settings | None = None,
    runtime_loader: RuntimeLoader = DetectionRuntime.load,
) -> FastAPI:
    resolved_settings = settings or Settings.load(Path(__file__).resolve().parents[2])

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = resolved_settings
        try:
            app.state.runtime = runtime_loader(resolved_settings)
        except Exception:
            app.state.runtime = None
        app.state.job_storage = JobStorage(resolved_settings.project_root / ".runtime" / "jobs")
        app.state.job_storage.cleanup_expired()
        app.state.job_manager = (
            JobManager(app.state.job_storage, VideoProcessor(app.state.runtime), max_concurrency=1)
            if app.state.runtime is not None else None
        )
        async def cleanup():
            while True:
                await asyncio.sleep(60)
                removed = app.state.job_storage.cleanup_expired()
                if app.state.job_manager is not None:
                    app.state.job_manager.expire(removed)

        sweeper = asyncio.create_task(cleanup())
        try:
            yield
        finally:
            sweeper.cancel()
            with suppress(asyncio.CancelledError):
                await sweeper
            if app.state.job_manager is not None:
                await app.state.job_manager.close()

    application = FastAPI(title="Vehicle Detection API", lifespan=lifespan)

    @application.exception_handler(ApplicationError)
    async def handle_application_error(_: Request, exc: ApplicationError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    application.include_router(health_router)
    application.include_router(images_router)
    application.include_router(live_router)
    application.include_router(videos_router)
    return application


app = create_app()
