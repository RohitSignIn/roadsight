import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from backend.app.jobs.storage import JobStorage


def test_create_uses_job_id_beneath_storage_root_and_not_user_filename(tmp_path: Path) -> None:
    storage = JobStorage(tmp_path / "jobs", ttl=timedelta(minutes=30))
    job_id = uuid4()

    paths = storage.create(job_id)

    assert paths.root == (tmp_path / "jobs" / str(job_id)).resolve()
    assert paths.input_dir.parent == paths.root
    assert paths.output_dir.parent == paths.root
    assert paths.input_dir.is_dir()
    assert paths.output_dir.is_dir()


def test_cleanup_skips_expired_job_while_download_is_leased(tmp_path: Path) -> None:
    storage = JobStorage(tmp_path / "jobs", ttl=timedelta(seconds=1))
    job_id = uuid4()
    paths = storage.create(job_id)
    old = (datetime.now(UTC) - timedelta(hours=1)).timestamp()
    os.utime(paths.root, (old, old))

    with storage.lease(job_id):
        assert storage.cleanup_expired(datetime.now(UTC)) == []
        assert paths.root.exists()

    assert storage.cleanup_expired(datetime.now(UTC)) == [job_id]
    assert not paths.root.exists()


def test_cleanup_removes_abandoned_expired_directories_on_startup(tmp_path: Path) -> None:
    storage = JobStorage(tmp_path / "jobs", ttl=timedelta(seconds=1))
    job_id = uuid4()
    paths = storage.create(job_id)
    old = (datetime.now(UTC) - timedelta(days=1)).timestamp()
    os.utime(paths.root, (old, old))

    removed = storage.cleanup_expired(datetime.now(UTC))

    assert removed == [job_id]
    assert not paths.root.exists()

