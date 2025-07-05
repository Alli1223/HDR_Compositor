import sys
from pathlib import Path
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT.parent))

from HDR_Compositor.hdr_utils import (
    get_medium_exposure_image,
    enhance_image,
    tonemap_mantiuk,
    align_images,
    remove_ghosts,
)
from HDR_Compositor.find_and_merge_aeb import create_hdr


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


def test_align_and_deghost():
    img1 = np.zeros((10, 10, 3), dtype=np.uint8)
    cv2.rectangle(img1, (2, 2), (7, 7), (255, 255, 255), -1)
    img2 = np.roll(img1, 1, axis=1)
    aligned = align_images([img1, img2])
    diff = np.abs(aligned[0].astype(int) - aligned[1].astype(int)).sum()
    assert diff < 100

    ghosted = img1.copy()
    ghosted[5, 5] = [0, 0, 255]
    deghosted = remove_ghosts([img1, ghosted], threshold=10)
    assert tuple(deghosted[1][5, 5]) == tuple(img1[5, 5])
