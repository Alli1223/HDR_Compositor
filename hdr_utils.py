import cv2
import numpy as np
from typing import List, Sequence, Optional


def get_medium_exposure_image(
    images: Sequence[np.ndarray], exposure_times: Sequence[float]
) -> Optional[np.ndarray]:
    """Return the image with the median exposure time."""
    if not images or not exposure_times:
        return None
    pairs = sorted(zip(exposure_times, images), key=lambda x: x[0])
    _, sorted_images = zip(*pairs)
    return sorted_images[len(sorted_images) // 2]


def enhance_image(
    img: np.ndarray, reference: Optional[np.ndarray] = None
) -> np.ndarray:
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
        img = cv2.addWeighted(
            img.astype(np.float32), 0.7, ref.astype(np.float32), 0.3, 0
        )
        img = img.astype(np.uint8)
    return img


def tonemap_mantiuk(
    hdr_image: np.ndarray,
    reference_image: Optional[np.ndarray] = None,
    *,
    saturation: float = 1.0,
    contrast: float = 1.0,
    gamma: float = 1.0,
    brightness: float = 1.0,
) -> np.ndarray:
    """Tonemap an HDR image using the Mantiuk algorithm.

    Parameters allow adjusting the overall look of the result:
    ``saturation`` and ``contrast`` are forwarded to OpenCV's Mantiuk
    tonemapper. ``gamma`` controls global contrast and ``brightness`` scales
    the tone mapped image before conversion to 8‑bit.

    OpenCV's tonemapping expects the input HDR values to be in the ``0..1``
    range. Real world radiance maps can easily exceed this, leading to
    negative or clipped values after tonemapping which in turn may produce
    black pixels in very bright areas. Normalising the HDR data before
    tonemapping keeps highlights white and prevents those artefacts."""

    # Normalise to 0..1 to avoid extreme values causing dark highlights
    hdr_norm = cv2.normalize(
        hdr_image, None, alpha=0.0, beta=1.0, norm_type=cv2.NORM_MINMAX
    )

    tonemap = cv2.createTonemapMantiuk(
        gamma=gamma, scale=contrast, saturation=saturation
    )
    ldr = tonemap.process(hdr_norm.copy())
    # Apply additional brightness adjustment before converting to 8 bit
    ldr = np.clip(ldr * brightness, 0.0, 1.0)
    # Replace any NaN or infinity values before converting to 8 bit
    ldr = np.nan_to_num(ldr, nan=0.0, posinf=1.0, neginf=0.0)
    ldr_8bit = np.clip(ldr * 255, 0, 255).astype("uint8")
    return enhance_image(ldr_8bit, reference_image)


def align_images(images: List[np.ndarray]) -> List[np.ndarray]:
    """Align images to the first image using phase correlation."""
    if not images:
        return images
    aligned = [images[0]]
    ref_gray = cv2.cvtColor(images[0], cv2.COLOR_BGR2GRAY)
    for img in images[1:]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        shift = cv2.phaseCorrelate(np.float32(ref_gray), np.float32(gray))[0]
        matrix = np.float32([[1, 0, shift[0]], [0, 1, shift[1]]])
        aligned_img = cv2.warpAffine(
            img,
            matrix,
            (img.shape[1], img.shape[0]),
            flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
        )
        aligned.append(aligned_img)
    return aligned


def remove_ghosts(images: List[np.ndarray], threshold: int = 25) -> List[np.ndarray]:
    """Replace pixels that deviate from the median with the reference image.

    This version uses vectorised numpy operations for improved performance
    when processing many images."""
    if not images:
        return images

    stack = np.stack(images).astype(np.float32)
    median = np.median(stack, axis=0)
    reference = stack[0]

    # Compute absolute deviation for the whole stack in one operation
    diff = np.abs(stack - median).sum(axis=3)
    mask = diff > threshold

    # Replace deviating pixels with the reference image for all frames
    stack = np.where(mask[..., None], reference, stack)

    return [frame.astype(np.uint8) for frame in stack]
