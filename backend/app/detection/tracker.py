from __future__ import annotations

from types import SimpleNamespace
from threading import Lock

import numpy as np
from numpy.typing import NDArray
from ultralytics.trackers.byte_tracker import BYTETracker

from backend.app.schemas import Box, Detection, TrackedDetection


_TRACKER_LOCK = Lock()


class _ConcurrentByteTracker(BYTETracker):
    @staticmethod
    def reset_id():
        # IDs are allocated globally by Ultralytics. Resetting here corrupts
        # identities in other running sessions; analytics maps them locally.
        pass


class _ByteDetections:
    def __init__(self, xyxy: np.ndarray, conf: np.ndarray, cls: np.ndarray) -> None:
        self.xyxy = xyxy
        self.conf = conf
        self.cls = cls

    @property
    def xywh(self) -> np.ndarray:
        xywh = self.xyxy.copy()
        xywh[:, 0] = (self.xyxy[:, 0] + self.xyxy[:, 2]) / 2
        xywh[:, 1] = (self.xyxy[:, 1] + self.xyxy[:, 3]) / 2
        xywh[:, 2] = self.xyxy[:, 2] - self.xyxy[:, 0]
        xywh[:, 3] = self.xyxy[:, 3] - self.xyxy[:, 1]
        return xywh

    def __getitem__(self, item) -> "_ByteDetections":
        return _ByteDetections(self.xyxy[item], self.conf[item], self.cls[item])

    def __len__(self) -> int:
        return len(self.conf)


class TrackerSession:
    def __init__(self, *, track_buffer: int = 30) -> None:
        args = SimpleNamespace(
            track_high_thresh=0.25,
            track_low_thresh=0.1,
            new_track_thresh=0.25,
            track_buffer=track_buffer,
            match_thresh=0.8,
            fuse_score=True,
        )
        self._tracker = _ConcurrentByteTracker(args)

    def update(
        self,
        frame: NDArray[np.uint8],
        detections: list[Detection],
        timestamp_s: float,
    ) -> list[TrackedDetection]:
        del timestamp_s
        if detections:
            xyxy = np.array([list(item.box.model_dump().values()) for item in detections], dtype=np.float32)
            conf = np.array([item.confidence for item in detections], dtype=np.float32)
            cls = np.array([item.class_id for item in detections], dtype=np.float32)
        else:
            xyxy = np.empty((0, 4), dtype=np.float32)
            conf = np.empty((0,), dtype=np.float32)
            cls = np.empty((0,), dtype=np.float32)
        with _TRACKER_LOCK:
            results = self._tracker.update(_ByteDetections(xyxy, conf, cls), frame)
        height, width = frame.shape[:2]
        frame_area = float(height * width)
        tracked: list[TrackedDetection] = []
        for row in results:
            x1, y1, x2, y2, track_id, score, class_id, detection_index = row[:8]
            source_index = int(detection_index)
            class_name = detections[source_index].class_name
            detection = Detection(
                class_id=int(class_id),
                class_name=class_name,
                confidence=float(score),
                box=Box(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2)),
            )
            tracked.append(
                TrackedDetection(
                    track_id=int(track_id),
                    detection=detection,
                    relative_size=max(0.0, x2 - x1) * max(0.0, y2 - y1) / frame_area,
                )
            )
        return tracked
