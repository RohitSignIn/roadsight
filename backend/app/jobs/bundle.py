from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from backend.app.jobs.storage import JobPaths
from backend.app.schemas import VehicleRecord


CSV_COLUMNS = [
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


class BundleWriter:
    def write_image_result(
        self,
        *,
        paths: JobPaths,
        annotated_media: Path,
        records: list[VehicleRecord],
        metadata: dict,
        representative_crops: dict[int, Path] | None = None,
    ) -> Path:
        return self._write(
            paths=paths,
            annotated_media=annotated_media,
            media_name="processed_image.jpg",
            records=records,
            metadata=metadata,
            representative_crops=representative_crops or {},
        )

    def write_video_result(
        self,
        *,
        paths: JobPaths,
        annotated_media: Path,
        records: list[VehicleRecord],
        metadata: dict,
        representative_crops: dict[int, Path] | None = None,
    ) -> Path:
        return self._write(
            paths=paths,
            annotated_media=annotated_media,
            media_name="processed_video.mp4",
            records=records,
            metadata=metadata,
            representative_crops=representative_crops or {},
        )

    def _write(
        self,
        *,
        paths: JobPaths,
        annotated_media: Path,
        media_name: str,
        records: list[VehicleRecord],
        metadata: dict,
        representative_crops: dict[int, Path],
    ) -> Path:
        final_path = paths.root / "result.zip"
        temporary_path = paths.root / "result.zip.tmp"
        rows = [record.model_dump(mode="json") for record in records]
        csv_buffer = io.StringIO(newline="")
        writer = csv.DictWriter(csv_buffer, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        history = {**metadata, "vehicles": rows}
        summary = {
            "total_unique_vehicles": len(records),
            "counts_by_type": dict(sorted(Counter(record.vehicle_type for record in records).items())),
        }

        with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(annotated_media, media_name)
            archive.writestr("vehicle_history.csv", csv_buffer.getvalue())
            archive.writestr("vehicle_history.json", json.dumps(history, indent=2))
            archive.writestr("summary.json", json.dumps(summary, indent=2))
            for vehicle_id, crop_path in sorted(representative_crops.items()):
                archive.write(crop_path, f"vehicle_crops/vehicle_{vehicle_id}.jpg")
        temporary_path.replace(final_path)
        return final_path
