from backend.app.analytics.history import HistoryStore
from backend.app.schemas import Box, Detection, TrackedDetection


def tracked(confidence: float, color: str, direction: str, size: float) -> TrackedDetection:
    return TrackedDetection(
        track_id=7,
        detection=Detection(
            class_id=3,
            class_name="car",
            confidence=confidence,
            box=Box(x1=0, y1=0, x2=10, y2=10),
        ),
        color=color,
        direction=direction,
        relative_size=size,
    )


def test_history_aggregates_repeated_frames_into_one_vehicle_record() -> None:
    history = HistoryStore()
    history.observe(tracked(0.6, "white", "stationary", 0.10), timestamp_s=1.0)
    history.observe(tracked(0.9, "white", "right", 0.15), timestamp_s=3.5)
    history.observe(tracked(0.75, "gray", "right", 0.12), timestamp_s=4.0)

    records = history.records()

    assert len(records) == 1
    record = records[0]
    assert record.vehicle_id == 7
    assert record.vehicle_type == "car"
    assert record.color == "white"
    assert record.first_seen == 1.0
    assert record.last_seen == 4.0
    assert record.duration_seconds == 3.0
    assert record.average_confidence == 0.75
    assert record.maximum_confidence == 0.9
    assert record.relative_size == 0.15
    assert record.direction == "right"

