"""Shared tracking analytics for a single video or webcam session."""
import cv2
import numpy as np

from backend.app.analytics.color import estimate_color
from backend.app.analytics.direction import DirectionEstimator
from backend.app.analytics.history import HistoryStore
from backend.app.detection.tracker import TrackerSession


class CameraMotion:
    def __init__(self):
        self.previous = None

    def update(self, frame):
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160, 120))
        previous, self.previous = self.previous, gray
        if previous is None:
            return 0.0
        points = cv2.goodFeaturesToTrack(previous, 80, 0.02, 8)
        if points is None or len(points) < 8:
            return 1.0  # Insufficient evidence to rule out camera movement.
        moved, status, _ = cv2.calcOpticalFlowPyrLK(previous, gray, points, None)
        if moved is None or status is None:
            return 1.0
        valid = status.reshape(-1) == 1
        if valid.sum() < 8:
            return 1.0
        delta = (moved[valid] - points[valid]).reshape(-1, 2) / (160, 120)
        return float(np.linalg.norm(np.median(delta, axis=0)))


class AnalyticsSession:
    def __init__(self):
        self.tracker = TrackerSession()
        self.history = HistoryStore()
        self.direction = DirectionEstimator(camera_motion_limit=0.008)
        self.motion = CameraMotion()
        self.ids = {}

    def observe(self, frame, detections, timestamp):
        motion = self.motion.update(frame)
        height, width = frame.shape[:2]
        enriched = []
        for item in self.tracker.update(frame, detections, timestamp):
            # ByteTrack's underlying allocator is global; expose session-local IDs.
            local_id = self.ids.setdefault(item.track_id, len(self.ids) + 1)
            box = item.detection.box
            x1, x2 = [max(0, min(width, int(x))) for x in (box.x1, box.x2)]
            y1, y2 = [max(0, min(height, int(y))) for y in (box.y1, box.y2)]
            crop = frame[y1:y2, x1:x2]
            direction = self.direction.update(
                local_id, ((box.x1 + box.x2)/2, (box.y1 + box.y2)/2),
                frame.shape, timestamp, motion,
            )
            item = item.model_copy(update={
                "track_id": local_id, "color": estimate_color(crop).label, "direction": direction,
            })
            self.history.observe(item, timestamp)
            enriched.append((item, crop))
        return enriched
