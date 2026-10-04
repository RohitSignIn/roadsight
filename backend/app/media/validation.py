import cv2
import numpy as np
from numpy.typing import NDArray

from backend.app.errors import InvalidMediaError


def decode_image(data: bytes) -> NDArray[np.uint8]:
    if not data:
        raise InvalidMediaError("The uploaded file is not a valid image.")
    encoded = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise InvalidMediaError("The uploaded file is not a valid image.")
    return image
