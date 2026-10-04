from collections import Counter
from dataclasses import dataclass, field

from backend.app.schemas import TrackedDetection, VehicleRecord


@dataclass(slots=True)
class _Aggregate:
    vehicle_type: str
    first_seen: float
    last_seen: float
    confidence_sum: float
    observations: int
    maximum_confidence: float
    relative_size: float
    direction: str
    colors: Counter[str] = field(default_factory=Counter)


class HistoryStore:
    def __init__(self) -> None:
        self._tracks: dict[int, _Aggregate] = {}

    def observe(self, tracked: TrackedDetection, timestamp_s: float) -> None:
        aggregate = self._tracks.get(tracked.track_id)
        if aggregate is None:
            aggregate = _Aggregate(
                vehicle_type=tracked.detection.class_name,
                first_seen=timestamp_s,
                last_seen=timestamp_s,
                confidence_sum=0.0,
                observations=0,
                maximum_confidence=0.0,
                relative_size=0.0,
                direction="stationary",
            )
            self._tracks[tracked.track_id] = aggregate
        aggregate.last_seen = timestamp_s
        aggregate.confidence_sum += tracked.detection.confidence
        aggregate.observations += 1
        aggregate.maximum_confidence = max(aggregate.maximum_confidence, tracked.detection.confidence)
        aggregate.relative_size = max(aggregate.relative_size, tracked.relative_size)
        if tracked.color != "unknown":
            aggregate.colors[tracked.color] += 1
        if tracked.direction != "stationary" or aggregate.direction == "stationary":
            aggregate.direction = tracked.direction

    def records(self) -> list[VehicleRecord]:
        records: list[VehicleRecord] = []
        for track_id, aggregate in sorted(self._tracks.items()):
            color = aggregate.colors.most_common(1)[0][0] if aggregate.colors else "unknown"
            records.append(
                VehicleRecord(
                    vehicle_id=track_id,
                    vehicle_type=aggregate.vehicle_type,
                    color=color,
                    first_seen=aggregate.first_seen,
                    last_seen=aggregate.last_seen,
                    duration_seconds=aggregate.last_seen - aggregate.first_seen,
                    direction=aggregate.direction,
                    average_confidence=aggregate.confidence_sum / aggregate.observations,
                    maximum_confidence=aggregate.maximum_confidence,
                    relative_size=aggregate.relative_size,
                )
            )
        return records
