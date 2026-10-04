from collections import defaultdict, deque


class DirectionEstimator:
    def __init__(
        self,
        *,
        min_displacement: float = 0.03,
        camera_motion_limit: float = 0.08,
        window_size: int = 8,
    ) -> None:
        self.min_displacement = min_displacement
        self.camera_motion_limit = camera_motion_limit
        self._paths: dict[int, deque[tuple[float, float, float]]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )

    def update(
        self,
        track_id: int,
        center: tuple[float, float],
        frame_shape: tuple[int, int] | tuple[int, int, int],
        timestamp_s: float,
        camera_motion: float,
    ) -> str:
        height, width = frame_shape[:2]
        path = self._paths[track_id]
        path.append((center[0] / width, center[1] / height, timestamp_s))
        if camera_motion > self.camera_motion_limit:
            return "uncertain"
        if len(path) < 2:
            return "stationary"

        dx = path[-1][0] - path[0][0]
        dy = path[-1][1] - path[0][1]
        horizontal = "right" if dx >= self.min_displacement else "left" if dx <= -self.min_displacement else ""
        vertical = "down" if dy >= self.min_displacement else "up" if dy <= -self.min_displacement else ""
        if vertical and horizontal:
            return f"{vertical}-{horizontal}"
        return horizontal or vertical or "stationary"
