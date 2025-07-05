import sys
from pathlib import Path
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from hdr_utils import get_medium_exposure_image, enhance_image, tonemap_mantiuk
from find_and_merge_aeb import create_hdr


def test_get_medium_exposure_image():
    imgs = [np.full((2, 2, 3), i, dtype=np.uint8) for i in (10, 20, 30)]
    exposures = [0.1, 0.5, 1.0]
    result = get_medium_exposure_image(imgs, exposures)
    assert np.array_equal(result, imgs[1])


def test_enhance_and_tonemap():
    base = np.arange(16*3, dtype=np.uint8).reshape(4, 4, 3)
    images = [base, base + 20, base + 40]
    times = [1/30, 1/60, 1/125]
    hdr = create_hdr(images, times)
    ldr = tonemap_mantiuk(hdr)
    assert ldr.dtype == np.uint8
    assert ldr.shape == images[0].shape
    enhanced = enhance_image(images[0], reference=images[1])
    assert enhanced.shape == images[0].shape
