from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from threading import RLock

import numpy as np
from numpy.typing import NDArray

from backend.app.config import Settings
from backend.app.errors import ModelUnavailableError
from backend.app.schemas import Box, Detection


def select_device(cuda_available: bool) -> str:
    return "0" if cuda_available else "cpu"


def _default_cuda_available() -> bool:
    import torch

    return bool(torch.cuda.is_available())


def _default_model_loader(path: str) -> Any:
    from ultralytics import YOLO

    return YOLO(path)


def _to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value)


class DetectionRuntime:
    def __init__(self, *, settings: Settings, model: Any, device: str) -> None:
        self.settings = settings
        self._model = model
        self._lock = RLock()
        self.device = device
        self.class_names = {int(key): str(name) for key, name in model.names.items()}

    @classmethod
    def load(
        cls,
        settings: Settings,
        *,
        model_loader: Callable[[str], Any] = _default_model_loader,
        cuda_available: Callable[[], bool] = _default_cuda_available,
        warmup: bool = True,
    ) -> "DetectionRuntime":
        if not settings.model_path.is_file():
            raise ModelUnavailableError(f"Model checkpoint not found: {settings.model_path}")
        model = model_loader(str(settings.model_path))
        runtime = cls(settings=settings, model=model, device=select_device(cuda_available()))
        if warmup:
            runtime.warmup()
        return runtime

    def warmup(self) -> None:
        size = self.settings.inference_size
        self.detect(np.zeros((size, size, 3), dtype=np.uint8))

    @property
    def model_name(self) -> str:
        return Path(self.settings.model_path).name

    def detect(
        self,
        frame: NDArray[np.uint8],
        confidence: float | None = None,
    ) -> list[Detection]:
        # One shared model serves video workers, image requests and live sessions.
        with self._lock:
            return self._detect(frame, confidence)

    def _detect(
        self,
        frame: NDArray[np.uint8],
        confidence: float | None = None,
    ) -> list[Detection]:
        threshold = self.settings.confidence_threshold if confidence is None else confidence
        results = self._model.predict(
            source=frame,
            conf=threshold,
            imgsz=self.settings.inference_size,
            device=self.device,
            verbose=False,
        )
        detections: list[Detection] = []
        for result in results:
            boxes = result.boxes
            coordinates = _to_numpy(boxes.xyxy)
            confidences = _to_numpy(boxes.conf)
            classes = _to_numpy(boxes.cls)
            for xyxy, score, class_value in zip(coordinates, confidences, classes, strict=True):
                class_id = int(class_value)
                detections.append(
                    Detection(
                        class_id=class_id,
                        class_name=self.class_names[class_id],
                        confidence=float(score),
                        box=Box(x1=float(xyxy[0]), y1=float(xyxy[1]), x2=float(xyxy[2]), y2=float(xyxy[3])),
                    )
                )
        return detections
