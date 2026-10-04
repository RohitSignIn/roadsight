import csv
import json
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from backend.app.jobs.bundle import BundleWriter, CSV_COLUMNS
from backend.app.jobs.storage import JobStorage
from backend.app.schemas import VehicleRecord


def vehicle() -> VehicleRecord:
    return VehicleRecord(
        vehicle_id=4,
        vehicle_type="car",
        color="white",
        first_seen=1.25,
        last_seen=4.5,
        duration_seconds=3.25,
        direction="right",
        average_confidence=0.8,
        maximum_confidence=0.93,
        relative_size=0.12,
    )


def test_video_bundle_contains_media_reports_summary_and_representative_crop(tmp_path: Path) -> None:
    paths = JobStorage(tmp_path / "jobs").create(uuid4())
    video = paths.output_dir / "annotated.mp4"
    video.write_bytes(b"video")
    crop = paths.output_dir / "vehicle-4.jpg"
    crop.write_bytes(b"crop")

    bundle = BundleWriter().write_video_result(
        paths=paths,
        annotated_media=video,
        records=[vehicle()],
        metadata={"source": {"filename": "traffic.mp4"}, "model": "best.pt", "warnings": []},
        representative_crops={4: crop},
    )

    with ZipFile(bundle) as archive:
        assert set(archive.namelist()) == {
            "processed_video.mp4",
            "vehicle_history.csv",
            "vehicle_history.json",
            "summary.json",
            "vehicle_crops/vehicle_4.jpg",
        }
        rows = list(csv.DictReader(archive.read("vehicle_history.csv").decode().splitlines()))
        assert rows[0]["vehicle_id"] == "4"
        assert rows[0]["vehicle_type"] == "car"
        history = json.loads(archive.read("vehicle_history.json"))
        assert history["vehicles"][0]["direction"] == "right"
        assert history["source"]["filename"] == "traffic.mp4"
        summary = json.loads(archive.read("summary.json"))
        assert summary == {"total_unique_vehicles": 1, "counts_by_type": {"car": 1}}


def test_csv_columns_match_download_contract() -> None:
    assert CSV_COLUMNS == [
        "vehicle_id",
        "vehicle_type",
        "color",
        "first_seen",
        "last_seen",
        "duration_seconds",
        "direction",
        "average_confidence",
        "maximum_confidence",
        "relative_size",
    ]
