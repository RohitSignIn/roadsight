from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
import subprocess
import tempfile
import time

import cv2
from imageio_ffmpeg import get_ffmpeg_exe
from backend.app.analytics.session import AnalyticsSession
from backend.app.media.annotate import annotate_frame
from backend.app.schemas import VehicleRecord


class ProcessingCancelled(Exception):
    pass


class CancellationToken:
    def __init__(self):
        self._event = Event()

    @property
    def cancelled(self):
        return self._event.is_set()

    def cancel(self):
        self._event.set()

    def raise_if_cancelled(self):
        if self.cancelled:
            raise ProcessingCancelled()


@dataclass(frozen=True, slots=True)
class CompletedVideo:
    output: Path
    records: list[VehicleRecord]
    frame_count: int
    fps: float
    duration_seconds: float
    crops: dict[int, Path] = field(default_factory=dict)


def encode_video(source, output, cancel):
    command = [get_ffmpeg_exe(), "-nostdin", "-y", "-i", str(source), "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-movflags", "+faststart", str(output)]
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=errors,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            started = time.monotonic()
            while process.poll() is None:
                cancel.raise_if_cancelled()
                if time.monotonic() - started > 600:
                    raise RuntimeError("Video encoding timed out.")
                cancel._event.wait(0.05)
            if process.returncode:
                raise RuntimeError("Video encoding failed.")
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()


class VideoProcessor:
    def __init__(self, runtime):
        self.runtime = runtime

    def process(self, *, source, output, confidence, progress, cancel):
        capture = cv2.VideoCapture(str(source))
        writer = None
        intermediate = output.with_suffix(".avi")
        crops, scores = {}, {}
        session = AnalyticsSession()
        processed = 0
        try:
            if not capture.isOpened():
                raise ValueError("The uploaded file is not a valid video.")
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            width, height = (int(capture.get(key)) for key in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT))
            if not 0 < fps <= 1000 or min(width,height) <= 0:
                raise ValueError("The uploaded file is not a valid video.")
            output.parent.mkdir(parents=True, exist_ok=True)
            writer = cv2.VideoWriter(str(intermediate), cv2.VideoWriter_fourcc(*"MJPG"), fps, (width,height))
            if not writer.isOpened():
                raise RuntimeError("Could not initialize the video encoder.")
            while True:
                cancel.raise_if_cancelled()
                ok, frame = capture.read()
                if not ok:
                    break
                detections = self.runtime.detect(frame, confidence)
                observed = session.observe(frame, detections, processed/fps)
                for item, crop in observed:
                    score = crop.size * item.detection.confidence
                    if crop.size and score > scores.get(item.track_id, -1):
                        crop_path = output.parent / f"vehicle_{item.track_id}.jpg"
                        if cv2.imwrite(str(crop_path), crop):
                            crops[item.track_id] = crop_path
                            scores[item.track_id] = score
                writer.write(annotate_frame(frame, detections))
                processed += 1
                progress(min(0.9, 0.9 * processed / total) if total else 0)
            if processed == 0 or (total > 0 and processed < total - 1):
                raise ValueError("The uploaded file is not a valid video or is truncated.")
            writer.release(); writer = None
            capture.release()
            cancel.raise_if_cancelled()
            encode_video(intermediate, output, cancel)
            cancel.raise_if_cancelled()
            progress(1.0)
            return CompletedVideo(output, session.history.records(), processed, fps, processed/fps, crops)
        finally:
            capture.release()
            if writer is not None:
                writer.release()
            intermediate.unlink(missing_ok=True)
