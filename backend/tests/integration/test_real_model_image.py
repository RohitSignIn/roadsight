from pathlib import Path

import numpy as np
import pytest

from backend.app.config import Settings
from backend.app.detection.runtime import DetectionRuntime


@pytest.mark.model
def test_real_checkpoint_returns_normalized_detection_list() -> None:
    project_root = Path(__file__).resolve().parents[3]
    settings = Settings.load(project_root)

    runtime = DetectionRuntime.load(settings, cuda_available=lambda: False)
    detections = runtime.detect(np.zeros((320, 480, 3), dtype=np.uint8), confidence=0.25)

    assert runtime.device == "cpu"
    assert runtime.model_name == "best.pt"
    assert isinstance(detections, list)
    assert all(0.0 <= detection.confidence <= 1.0 for detection in detections)
