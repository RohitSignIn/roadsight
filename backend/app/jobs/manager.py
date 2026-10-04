import asyncio
import shutil
from dataclasses import dataclass, field, replace
from enum import StrEnum
from uuid import UUID, uuid4

from backend.app.jobs.bundle import BundleWriter
from backend.app.media.video import CancellationToken, ProcessingCancelled
from backend.app.schemas import VehicleRecord


class JobStatus(StrEnum):
    QUEUED="queued"
    PROCESSING="processing"
    COMPLETED="completed"
    FAILED="failed"
    CANCELLED="cancelled"
    EXPIRED="expired"


@dataclass(frozen=True, slots=True)
class JobSnapshot:
    id: UUID
    status: JobStatus
    progress: float=0.0
    error: str|None=None
    download_ready: bool=False
    vehicles: list[VehicleRecord]=field(default_factory=list)
    preview_url: str|None=None


class JobManager:
    def __init__(self, storage, processor, *, max_concurrency=1):
        self.storage, self.processor = storage, processor
        self._semaphore=asyncio.Semaphore(max_concurrency)
        self._snapshots={}
        self._tokens={}
        self._tasks={}

    async def submit(self, data, suffix, confidence):
        job_id=uuid4()
        paths=self.storage.create(job_id)
        source=paths.input_dir / f"source{suffix}"
        source.write_bytes(data)
        snapshot=JobSnapshot(id=job_id,status=JobStatus.QUEUED)
        self._snapshots[job_id]=snapshot
        token=CancellationToken()
        self._tokens[job_id]=token
        self._tasks[job_id]=asyncio.create_task(self._run(job_id,source,confidence,token))
        return snapshot

    def get(self, job_id):
        snapshot=self._snapshots[job_id]
        if not self.storage.paths(job_id).root.exists():
            return replace(snapshot,status=JobStatus.EXPIRED,download_ready=False,preview_url=None)
        return snapshot

    async def wait(self, job_id):
        task=self._tasks.get(job_id)
        if task:
            await task
        return self.get(job_id)

    async def cancel(self, job_id):
        snapshot=self.get(job_id)
        if snapshot.status in (JobStatus.QUEUED,JobStatus.PROCESSING):
            self._tokens[job_id].cancel()
            self._snapshots[job_id]=replace(snapshot,status=JobStatus.CANCELLED)
        return self.get(job_id)

    async def _run(self, job_id, source, confidence, token):
        paths=self.storage.paths(job_id)
        loop=asyncio.get_running_loop()
        def update(value):
            current=self._snapshots[job_id]
            if current.status==JobStatus.PROCESSING:
                self._snapshots[job_id]=replace(current,progress=max(current.progress,min(.99,value)))
        with self.storage.lease(job_id):
            try:
                async with self._semaphore:
                    token.raise_if_cancelled()
                    self._snapshots[job_id]=replace(self.get(job_id),status=JobStatus.PROCESSING)
                    completed=await asyncio.to_thread(self.processor.process, source=source,
                        output=paths.output_dir/"processed_video.mp4",confidence=confidence,
                        progress=lambda value:loop.call_soon_threadsafe(update,value),cancel=token)
                    token.raise_if_cancelled()
                    await asyncio.to_thread(BundleWriter().write_video_result,
                        paths=paths,annotated_media=completed.output,records=completed.records,
                        metadata={"source":"uploaded_video","frames":completed.frame_count,"fps":completed.fps,
                                  "duration_seconds":completed.duration_seconds,
                                  "warnings":["Color and screen direction are estimates. Audio is omitted."]},
                        representative_crops=completed.crops)
                    token.raise_if_cancelled()
                    self._snapshots[job_id]=replace(self.get(job_id),status=JobStatus.COMPLETED,
                        progress=1.0,download_ready=True,vehicles=completed.records,
                        preview_url=f"/api/videos/{job_id}/preview")
            except ProcessingCancelled:
                self._snapshots[job_id]=replace(self.get(job_id),status=JobStatus.CANCELLED)
            except Exception:
                self._snapshots[job_id]=replace(self.get(job_id),status=JobStatus.FAILED,
                    error="Video processing failed. Check that the video is playable and FFmpeg is installed.")
            finally:
                source.unlink(missing_ok=True)
                if self._snapshots[job_id].status!=JobStatus.COMPLETED:
                    shutil.rmtree(paths.output_dir,ignore_errors=True)
                    paths.output_dir.mkdir(exist_ok=True)
                    (paths.root/"result.zip").unlink(missing_ok=True)
                    (paths.root/"result.zip.tmp").unlink(missing_ok=True)
                self.storage.touch(job_id)

    def expire(self, ids):
        for job_id in ids:
            self._snapshots.pop(job_id,None)
            self._tokens.pop(job_id,None)
            self._tasks.pop(job_id,None)

    async def close(self):
        for token in self._tokens.values():
            token.cancel()
        await asyncio.gather(*self._tasks.values(),return_exceptions=True)
