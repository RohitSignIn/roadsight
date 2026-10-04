import cv2
import numpy as np
import pytest

from backend.app.analytics.session import CameraMotion
from backend.app.media.video import CancellationToken, ProcessingCancelled, encode_video


def test_camera_motion_detects_global_translation():
    rng=np.random.default_rng(7)
    frame=rng.integers(0,256,(120,160,3),dtype=np.uint8)
    moved=cv2.warpAffine(frame,np.float32([[1,0,5],[0,1,0]]),(160,120))
    motion=CameraMotion()
    assert motion.update(frame)==0
    assert motion.update(moved)>.008


def test_featureless_camera_motion_is_uncertain():
    motion=CameraMotion()
    frame=np.zeros((120,160,3),dtype=np.uint8)
    motion.update(frame)
    assert motion.update(frame)==1


def test_encoder_failure_is_reported(tmp_path):
    source=tmp_path/"bad.avi"
    source.write_bytes(b"bad")
    with pytest.raises(RuntimeError,match="encoding failed"):
        encode_video(source,tmp_path/"out.mp4",CancellationToken())
