import cv2
import numpy as np
from typing import List, Sequence, Optional


def get_medium_exposure_image(images: Sequence[np.ndarray], exposure_times: Sequence[float]) -> Optional[np.ndarray]:
    """Return the image with the median exposure time."""
    if not images or not exposure_times:
        return None
    pairs = sorted(zip(exposure_times, images), key=lambda x: x[0])
    _, sorted_images = zip(*pairs)
    return sorted_images[len(sorted_images) // 2]


def enhance_image(img: np.ndarray, reference: Optional[np.ndarray] = None) -> np.ndarray:
    """Apply simple color and contrast enhancements."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.3, 0, 255)
    img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    img = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    if reference is not None:
        ref = cv2.resize(reference, (img.shape[1], img.shape[0]))
        img = cv2.addWeighted(img.astype(np.float32), 0.7, ref.astype(np.float32), 0.3, 0)
        img = img.astype(np.uint8)
    return img


def tonemap_mantiuk(hdr_image: np.ndarray, reference_image: Optional[np.ndarray] = None) -> np.ndarray:
    """Tonemap an HDR image using Mantiuk algorithm and enhance the result."""
    tonemap = cv2.createTonemapMantiuk()
    tonemap.setSaturation(1.6)
    tonemap.setScale(0.7)
    ldr = tonemap.process(hdr_image.copy())
    ldr_8bit = np.clip(ldr * 255, 0, 255).astype("uint8")
    return enhance_image(ldr_8bit, reference_image)
