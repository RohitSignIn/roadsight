import numpy as np
import pytest

from backend.app.analytics.color import estimate_color


@pytest.mark.parametrize(
    ("bgr", "expected"),
    [
        ((10, 10, 10), "black"),
        ((245, 245, 245), "white"),
        ((125, 125, 125), "gray"),
        ((20, 20, 220), "red"),
        ((220, 30, 20), "blue"),
        ((30, 180, 30), "green"),
    ],
)
def test_estimate_color_classifies_broad_vehicle_colors(bgr, expected) -> None:
    crop = np.full((40, 60, 3), bgr, dtype=np.uint8)

    assert estimate_color(crop).label == expected


@pytest.mark.parametrize(
    "crop",
    [np.empty((0, 0, 3), dtype=np.uint8), np.zeros((2, 2, 3), dtype=np.uint8)],
)
def test_estimate_color_returns_unknown_for_empty_or_tiny_crops(crop) -> None:
    assert estimate_color(crop).label == "unknown"

