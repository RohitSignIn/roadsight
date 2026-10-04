import cv2
import numpy as np
from numpy.typing import NDArray

from backend.app.schemas import Detection


def annotate_frame(
    frame: NDArray[np.uint8],
    detections: list[Detection],
) -> NDArray[np.uint8]:
    annotated = frame.copy()
    height, width = annotated.shape[:2]
    for detection in detections:
        box = detection.box
        x1 = max(0, min(width - 1, round(box.x1)))
        y1 = max(0, min(height - 1, round(box.y1)))
        x2 = max(0, min(width - 1, round(box.x2)))
        y2 = max(0, min(height - 1, round(box.y2)))
        if x2 <= x1 or y2 <= y1:
            continue
        color = (38, 220, 110)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"{detection.class_name} {detection.confidence:.2f}"
        text_y = max(12, y1 - 5)
        cv2.putText(annotated, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    return annotated
