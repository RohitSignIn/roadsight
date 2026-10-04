from pathlib import Path

import cv2
import numpy as np
import pytest

from backend.app.media.video import CancellationToken, VideoProcessor
from backend.app.schemas import Box, Detection


class FakeRuntime:
    def detect(self, frame, confidence):
        return [Detection(class_id=0, class_name="car", confidence=0.9,
                          box=Box(x1=2, y1=2, x2=18, y2=18))]


def make_video(path: Path, frames: int = 3) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 12.0, (32, 24))
    assert writer.isOpened()
    for index in range(frames):
        writer.write(np.full((24, 32, 3), index * 20, dtype=np.uint8))
    writer.release()


def test_video_processor_preserves_fps_and_aggregates_unique_history(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    target = tmp_path / "processed.mp4"
    make_video(source)
    progress = []

    result = VideoProcessor(FakeRuntime()).process(
        source=source, output=target, confidence=0.25,
        progress=progress.append, cancel=CancellationToken(),
    )

    assert result.frame_count == 3
    assert result.fps == pytest.approx(12.0, rel=0.1)
    assert target.exists() and target.stat().st_size > 0
    assert len(result.records) == 1
    assert progress == sorted(progress)
    assert progress[-1] == 1.0


def test_video_processor_rejects_undecodable_content(tmp_path: Path) -> None:
    source = tmp_path / "fake.mp4"
    source.write_bytes(b"not video")
    with pytest.raises(ValueError, match="valid video"):
        VideoProcessor(FakeRuntime()).process(
            source=source, output=tmp_path / "out.mp4", confidence=0.25,
            progress=lambda _: None, cancel=CancellationToken(),
        )
