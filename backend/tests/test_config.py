from pathlib import Path

from backend.app.config import Settings


def test_settings_resolve_checkpoint_and_cpu_defaults_from_project_root(tmp_path: Path) -> None:
    settings = Settings.load(tmp_path)

    assert settings.project_root == tmp_path.resolve()
    assert settings.model_path == (tmp_path / "models" / "best.pt").resolve()
    assert settings.max_video_bytes == 10 * 1024 * 1024
    assert settings.inference_size == 640
    assert settings.confidence_threshold == 0.25

