import sys
from pathlib import Path
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT.parent))

from HDR_Compositor.find_and_merge_aeb import create_hdr
from HDR_Compositor.hdr_utils import tonemap_mantiuk


def test_reference_highlight_preserved():
    imgs = []
    vals = [40, 80, 160]
    for i, val in enumerate(vals):
        img = np.full((2, 2, 3), val, dtype=np.uint8)
        if i == 0:
            img[0, 0] = [255, 255, 255]
        imgs.append(img)
    times = [1.0, 0.5, 0.25]
    hdr = create_hdr(imgs, times)
    ref = imgs[1]
    ldr = tonemap_mantiuk(hdr, ref)
    assert ldr[0, 0].mean() >= 250


def test_large_bright_area_preserved():
    imgs = []
    vals = [40, 80, 160]
    for i, val in enumerate(vals):
        img = np.full((8, 8, 3), val, dtype=np.uint8)
        if i == 0:
            cv2.circle(img, (4, 4), 2, (255, 255, 255), -1)
        imgs.append(img)
    times = [1.0, 0.5, 0.25]
    hdr = create_hdr(imgs, times)
    ref = imgs[1]
    ldr = tonemap_mantiuk(hdr, ref)
    center = ldr[4, 4].mean()
    neighbour = ldr[4, 3].mean()
    assert center >= 250
    assert neighbour >= 250
