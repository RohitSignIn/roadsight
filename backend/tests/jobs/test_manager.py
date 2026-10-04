import asyncio
from pathlib import Path

import pytest

from backend.app.jobs.manager import JobManager, JobStatus
from backend.app.jobs.storage import JobStorage
from backend.app.media.video import CancellationToken, CompletedVideo


class BlockingProcessor:
    def process(self, *, source, output, confidence, progress, cancel: CancellationToken):
        progress(0.2)
        while not cancel.cancelled:
            import time
            time.sleep(0.005)
        cancel.raise_if_cancelled()


@pytest.mark.asyncio
async def test_job_lifecycle_progress_and_cancellation(tmp_path: Path) -> None:
    manager = JobManager(JobStorage(tmp_path / "jobs"), BlockingProcessor(), max_concurrency=1)
    snapshot = await manager.submit(b"video", ".mp4", 0.25)
    assert snapshot.status in {JobStatus.QUEUED, JobStatus.PROCESSING}
    for _ in range(100):
        current = manager.get(snapshot.id)
        if current.progress >= 0.2:
            break
        await asyncio.sleep(0.01)
    cancelled = await manager.cancel(snapshot.id)
    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.progress >= 0.2


class SuccessfulProcessor:
    def process(self, *, source, output, confidence, progress, cancel):
        output.write_bytes(b"processed")
        progress(1.0)
        return CompletedVideo(output=output, records=[], frame_count=1, fps=10.0, duration_seconds=0.1)


@pytest.mark.asyncio
async def test_successful_job_reaches_completed(tmp_path: Path) -> None:
    manager = JobManager(JobStorage(tmp_path / "jobs"), SuccessfulProcessor(), max_concurrency=1)
    snapshot = await manager.submit(b"video", ".mp4", 0.25)
    final = await manager.wait(snapshot.id)
    assert final.status == JobStatus.COMPLETED
    assert final.progress == 1.0
    assert final.download_ready is True
