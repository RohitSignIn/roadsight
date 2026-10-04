import pytest

from backend.app.analytics.direction import DirectionEstimator


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ((20, 50), (80, 50), "right"),
        ((80, 50), (20, 50), "left"),
        ((50, 80), (50, 20), "up"),
        ((50, 20), (50, 80), "down"),
        ((20, 80), (80, 20), "up-right"),
        ((80, 20), (20, 80), "down-left"),
    ],
)
def test_direction_uses_normalized_smoothed_displacement(start, end, expected) -> None:
    estimator = DirectionEstimator(min_displacement=0.03, camera_motion_limit=0.08)
    assert estimator.update(1, start, (100, 100), 0.0, camera_motion=0.0) == "stationary"

    direction = estimator.update(1, end, (100, 100), 1.0, camera_motion=0.0)

    assert direction == expected


def test_direction_stays_stationary_below_minimum_displacement() -> None:
    estimator = DirectionEstimator(min_displacement=0.05, camera_motion_limit=0.08)
    estimator.update(1, (50, 50), (100, 100), 0.0, camera_motion=0.0)

    assert estimator.update(1, (52, 51), (100, 100), 1.0, camera_motion=0.0) == "stationary"


def test_direction_is_uncertain_when_camera_motion_is_excessive() -> None:
    estimator = DirectionEstimator(min_displacement=0.03, camera_motion_limit=0.08)
    estimator.update(1, (20, 50), (100, 100), 0.0, camera_motion=0.0)

    assert estimator.update(1, (80, 50), (100, 100), 1.0, camera_motion=0.2) == "uncertain"

