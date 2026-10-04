import cv2
import numpy as np

from backend.app.media.annotate import annotate_frame
from backend.app.media.image import ImageProcessor
from backend.app.schemas import Box, Detection


def car_detection(box: Box | None = None) -> Detection:
    return Detection(
        class_id=3,
        class_name="car",
        confidence=0.91,
        box=box or Box(x1=4, y1=5, x2=20, y2=18),
    )


def test_annotate_frame_clips_boxes_without_mutating_source() -> None:
    source = np.zeros((24, 32, 3), dtype=np.uint8)
    original = source.copy()
    detection = car_detection(Box(x1=-10, y1=-5, x2=100, y2=80))

    annotated = annotate_frame(source, [detection])

    assert np.array_equal(source, original)
    assert annotated.shape == source.shape
    assert np.any(annotated != source)


def test_image_processor_returns_jpeg_and_one_record_per_detection() -> None:
    source = np.zeros((24, 32, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", source)
    assert success

    class FakeRuntime:
        def detect(self, frame, confidence):
            assert frame.shape == source.shape
            assert confidence == 0.3
            return [car_detection()]

    result = ImageProcessor(FakeRuntime()).process(encoded.tobytes(), confidence=0.3)

    assert result.annotated_jpeg.startswith(b"\xff\xd8")
    assert len(result.vehicles) == 1
    assert result.vehicles[0].vehicle_id == 1
    assert result.vehicles[0].vehicle_type == "car"
    assert result.vehicles[0].maximum_confidence == 0.91


def test_image_processor_estimates_color_from_detected_vehicle_crop() -> None:
    source = np.zeros((40, 50, 3), dtype=np.uint8)
    source[5:30, 4:35] = (20, 20, 220)
    success, encoded = cv2.imencode(".png", source)
    assert success

    class FakeRuntime:
        def detect(self, frame, confidence):
            return [car_detection(Box(x1=4, y1=5, x2=35, y2=30))]

    result = ImageProcessor(FakeRuntime()).process(encoded.tobytes(), confidence=0.25)

    assert result.vehicles[0].color == "red"
