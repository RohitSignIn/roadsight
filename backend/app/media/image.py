from dataclasses import dataclass
from typing import Protocol

import cv2

from backend.app.analytics.color import estimate_color
from backend.app.media.annotate import annotate_frame
from backend.app.media.validation import decode_image
from backend.app.schemas import Detection, VehicleRecord


class Detector(Protocol):
    def detect(self, frame, confidence: float | None = None) -> list[Detection]: ...


@dataclass(frozen=True, slots=True)
class ImageResult:
    annotated_jpeg: bytes
    vehicles: list[VehicleRecord]


class ImageProcessor:
    def __init__(self, runtime: Detector) -> None:
        self._runtime = runtime

    def process(self, data: bytes, confidence: float) -> ImageResult:
        frame = decode_image(data)
        detections = self._runtime.detect(frame, confidence)
        height, width = frame.shape[:2]
        frame_area = float(height * width)
        vehicles: list[VehicleRecord] = []
        for index, detection in enumerate(detections, start=1):
            box = detection.box
            x1 = max(0, min(width, round(box.x1)))
            y1 = max(0, min(height, round(box.y1)))
            x2 = max(0, min(width, round(box.x2)))
            y2 = max(0, min(height, round(box.y2)))
            crop = frame[y1:y2, x1:x2]
            vehicles.append(
                VehicleRecord(
                    vehicle_id=index,
                    vehicle_type=detection.class_name,
                    color=estimate_color(crop).label,
                    first_seen=0.0,
                    last_seen=0.0,
                    duration_seconds=0.0,
                    average_confidence=detection.confidence,
                    maximum_confidence=detection.confidence,
                    relative_size=max(0.0, box.x2 - box.x1)
                    * max(0.0, box.y2 - box.y1)
                    / frame_area,
                )
            )
        annotated = annotate_frame(frame, detections)
        success, encoded = cv2.imencode(".jpg", annotated)
        if not success:
            raise RuntimeError("Could not encode annotated image")
        return ImageResult(annotated_jpeg=encoded.tobytes(), vehicles=vehicles)
