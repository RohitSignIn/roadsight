from pathlib import Path

import numpy as np

from backend.app.config import Settings
from backend.app.detection.runtime import DetectionRuntime, select_device


def test_select_device_uses_cpu_without_cuda() -> None:
    assert select_device(cuda_available=False) == "cpu"


def test_select_device_uses_first_cuda_device_when_available() -> None:
    assert select_device(cuda_available=True) == "0"


def test_runtime_loads_checkpoint_once_and_exposes_device(tmp_path: Path) -> None:
    checkpoint = tmp_path / "models" / "best.pt"
    checkpoint.parent.mkdir()
    checkpoint.write_bytes(b"checkpoint")
    loaded_paths: list[str] = []

    class FakeModel:
        names = {0: "car"}

    def load_model(path: str) -> FakeModel:
        loaded_paths.append(path)
        return FakeModel()

    settings = Settings.load(tmp_path)
    runtime = DetectionRuntime.load(
        settings,
        model_loader=load_model,
        cuda_available=lambda: False,
        warmup=False,
    )

    assert loaded_paths == [str(checkpoint.resolve())]
    assert runtime.device == "cpu"
    assert runtime.class_names == {0: "car"}


def test_runtime_converts_model_boxes_to_normalized_detections(tmp_path: Path) -> None:
    checkpoint = tmp_path / "models" / "best.pt"
    checkpoint.parent.mkdir()
    checkpoint.write_bytes(b"checkpoint")

    class FakeBoxes:
        xyxy = np.array([[10.0, 20.0, 110.0, 220.0]])
        conf = np.array([0.875])
        cls = np.array([0.0])

    class FakeResult:
        boxes = FakeBoxes()

    class FakeModel:
        names = {0: "car"}

        def predict(self, **kwargs):
            assert kwargs["conf"] == 0.4
            assert kwargs["imgsz"] == 640
            assert kwargs["device"] == "cpu"
            assert kwargs["verbose"] is False
            return [FakeResult()]

    runtime = DetectionRuntime.load(
        Settings.load(tmp_path),
        model_loader=lambda _: FakeModel(),
        cuda_available=lambda: False,
        warmup=False,
    )

    detections = runtime.detect(np.zeros((240, 320, 3), dtype=np.uint8), confidence=0.4)

    assert len(detections) == 1
    assert detections[0].class_id == 0
    assert detections[0].class_name == "car"
    assert detections[0].confidence == 0.875
    assert detections[0].box.model_dump() == {
        "x1": 10.0,
        "y1": 20.0,
        "x2": 110.0,
        "y2": 220.0,
    }


def test_runtime_warms_up_model_on_load(tmp_path: Path) -> None:
    checkpoint = tmp_path / "models" / "best.pt"
    checkpoint.parent.mkdir()
    checkpoint.write_bytes(b"checkpoint")
    shapes: list[tuple[int, ...]] = []

    class EmptyBoxes:
        xyxy = np.zeros((0, 4))
        conf = np.zeros(0)
        cls = np.zeros(0)

    class FakeResult:
        boxes = EmptyBoxes()

    class FakeModel:
        names = {0: "car"}

        def predict(self, **kwargs):
            shapes.append(kwargs["source"].shape)
            return [FakeResult()]

    DetectionRuntime.load(
        Settings.load(tmp_path),
        model_loader=lambda _: FakeModel(),
        cuda_available=lambda: False,
    )

    assert shapes == [(640, 640, 3)]
