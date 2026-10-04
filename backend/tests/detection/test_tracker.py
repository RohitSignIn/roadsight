import numpy as np

from backend.app.detection.tracker import TrackerSession
from backend.app.schemas import Box, Detection


def car(x1: float = 10, x2: float = 30) -> Detection:
    return Detection(
        class_id=3,
        class_name="car",
        confidence=0.9,
        box=Box(x1=x1, y1=10, x2=x2, y2=30),
    )


def test_tracker_keeps_one_id_across_continuous_frames() -> None:
    tracker = TrackerSession(track_buffer=2)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    first = tracker.update(frame, [car()], timestamp_s=0.0)
    second = tracker.update(frame, [car(11, 31)], timestamp_s=0.1)

    assert len(first) == len(second) == 1
    assert first[0].track_id == second[0].track_id


def test_tracker_retains_id_after_brief_disappearance() -> None:
    tracker = TrackerSession(track_buffer=2)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    original_id = tracker.update(frame, [car()], timestamp_s=0.0)[0].track_id
    assert tracker.update(frame, [], timestamp_s=0.1) == []

    returned_id = tracker.update(frame, [car(11, 31)], timestamp_s=0.2)[0].track_id

    assert returned_id == original_id


def test_tracker_may_assign_new_id_after_long_disappearance() -> None:
    tracker = TrackerSession(track_buffer=1)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    original_id = tracker.update(frame, [car()], timestamp_s=0.0)[0].track_id
    tracker.update(frame, [], timestamp_s=0.1)
    tracker.update(frame, [], timestamp_s=0.2)
    tracker.update(frame, [], timestamp_s=0.3)

    assert tracker.update(frame, [car()], timestamp_s=0.4) == []
    returned_id = tracker.update(frame, [car(11, 31)], timestamp_s=0.5)[0].track_id

    assert returned_id != original_id
def test_starting_another_session_does_not_reset_existing_track_ids():
    import numpy as np
    from backend.app.schemas import Box, Detection
    from backend.app.detection.tracker import TrackerSession

    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    car = Detection(class_id=0, class_name="car", confidence=.9,
                    box=Box(x1=5, y1=5, x2=35, y2=35))
    truck = Detection(class_id=1, class_name="truck", confidence=.9,
                      box=Box(x1=120, y1=120, x2=160, y2=160))
    first = TrackerSession()
    initial_id = first.update(frame, [car], 0)[0].track_id
    second = TrackerSession()
    first.update(frame, [car, truck], .1)
    tracked = first.update(frame, [car, truck], .2)
    assert len({item.track_id for item in tracked}) == 2
    assert next(item.track_id for item in tracked if item.detection.class_name == "car") == initial_id
