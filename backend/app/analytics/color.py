from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class ColorSample:
    label: str
    confidence: float


def estimate_color(crop: NDArray[np.uint8]) -> ColorSample:
    if crop.ndim != 3 or crop.shape[0] < 8 or crop.shape[1] < 8 or crop.shape[2] != 3:
        return ColorSample("unknown", 0.0)

    height, width = crop.shape[:2]
    inset_y = max(1, round(height * 0.15))
    inset_x = max(1, round(width * 0.15))
    center = crop[inset_y : height - inset_y, inset_x : width - inset_x]
    if center.size == 0:
        return ColorSample("unknown", 0.0)

    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    hue, saturation, value = np.median(hsv.reshape(-1, 3), axis=0)

    if value <= 45:
        return ColorSample("black", 0.9)
    if saturation <= 35 and value >= 210:
        return ColorSample("white", 0.9)
    if saturation <= 40:
        return ColorSample("gray", 0.8)
    if hue < 10 or hue >= 170:
        return ColorSample("red", 0.8)
    if hue < 22:
        return ColorSample("orange", 0.8)
    if hue < 35:
        return ColorSample("yellow", 0.8)
    if hue < 85:
        return ColorSample("green", 0.8)
    if hue < 135:
        return ColorSample("blue", 0.8)
    return ColorSample("unknown", 0.0)
