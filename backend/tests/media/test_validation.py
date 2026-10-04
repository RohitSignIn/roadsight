import cv2
import numpy as np
import pytest

from backend.app.errors import InvalidMediaError
from backend.app.media.validation import decode_image


@pytest.mark.parametrize("extension", [".jpg", ".png"])
def test_decode_image_accepts_decodable_content_regardless_of_name(extension: str) -> None:
    source = np.full((12, 18, 3), 127, dtype=np.uint8)
    success, encoded = cv2.imencode(extension, source)
    assert success

    decoded = decode_image(encoded.tobytes())

    assert decoded.shape == (12, 18, 3)


@pytest.mark.parametrize("payload", [b"", b"this is not an image"])
def test_decode_image_rejects_empty_or_malformed_content(payload: bytes) -> None:
    with pytest.raises(InvalidMediaError, match="valid image"):
        decode_image(payload)

