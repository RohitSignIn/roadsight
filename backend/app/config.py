from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    model_path: Path
    max_video_bytes: int = 10 * 1024 * 1024
    inference_size: int = 640
    confidence_threshold: float = 0.25

    @classmethod
    def load(cls, project_root: Path) -> "Settings":
        root = project_root.resolve()
        return cls(project_root=root, model_path=(root / "models" / "best.pt").resolve())

