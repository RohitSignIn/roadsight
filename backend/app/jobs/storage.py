from __future__ import annotations

import shutil
import os
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True, slots=True)
class JobPaths:
    root: Path
    input_dir: Path
    output_dir: Path


class JobStorage:
    def __init__(self, root: Path, ttl: timedelta = timedelta(hours=1)) -> None:
        self.root = root.resolve()
        self.ttl = ttl
        self._leases: Counter[UUID] = Counter()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, job_id: UUID) -> JobPaths:
        job_root = (self.root / str(job_id)).resolve()
        if job_root.parent != self.root:
            raise ValueError("Job path escaped storage root")
        input_dir = job_root / "input"
        output_dir = job_root / "output"
        input_dir.mkdir(parents=True, exist_ok=False)
        output_dir.mkdir()
        return JobPaths(root=job_root, input_dir=input_dir, output_dir=output_dir)

    def paths(self, job_id: UUID) -> JobPaths:
        job_root = (self.root / str(job_id)).resolve()
        return JobPaths(root=job_root, input_dir=job_root / "input", output_dir=job_root / "output")

    @contextmanager
    def lease(self, job_id: UUID):
        self._leases[job_id] += 1
        try:
            yield self.paths(job_id)
        finally:
            self._leases[job_id] -= 1
            if self._leases[job_id] <= 0:
                del self._leases[job_id]

    def touch(self, job_id: UUID):
        os.utime(self.paths(job_id).root, None)

    def cleanup_expired(self, now: datetime | None = None) -> list[UUID]:
        current = now or datetime.now(UTC)
        removed: list[UUID] = []
        for child in sorted(self.root.iterdir()):
            if not child.is_dir():
                continue
            try:
                job_id = UUID(child.name)
            except ValueError:
                continue
            if job_id in self._leases:
                continue
            modified = datetime.fromtimestamp(child.stat().st_mtime, tz=UTC)
            if current - modified > self.ttl:
                shutil.rmtree(child)
                removed.append(job_id)
        return removed
