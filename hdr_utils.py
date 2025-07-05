import cv2
import numpy as np


def tonemap_mantiuk(hdr_image, saturation=1.2, scale=0.7):
    """Apply Mantiuk tonemapping and return an 8-bit image."""
    tonemap = cv2.createTonemapMantiuk()
    tonemap.setSaturation(saturation)
    tonemap.setScale(scale)
    ldr = tonemap.process(hdr_image.copy())
    return np.clip(ldr * 255, 0, 255).astype("uint8")

