"""Lease files until ASGI has completed sending (including disconnect/error)."""
from fastapi.responses import FileResponse
from backend.app.errors import JobNotFoundError


class LeasedFileResponse(FileResponse):
    def __init__(self, storage, job_id, path, **kwargs):
        self.storage, self.job_id = storage, job_id
        super().__init__(path, **kwargs)

    async def __call__(self, scope, receive, send):
        with self.storage.lease(self.job_id):
            if not self.storage.paths(self.job_id).root.exists():
                raise JobNotFoundError("This result has expired.")
            await super().__call__(scope, receive, send)
