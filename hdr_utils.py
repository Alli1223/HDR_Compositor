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


def tonemap(
    hdr_image: np.ndarray,
    reference_image: Optional[np.ndarray] = None,
    *,
    algorithm: str = "mantiuk",
    saturation: float = 1.0,
    contrast: float = 1.0,
    gamma: float = 1.0,
    brightness: float = 1.0,
) -> np.ndarray:
    """Tonemap an HDR image using different algorithms."""

    hdr_norm = cv2.normalize(
        hdr_image, None, alpha=0.0, beta=1.0, norm_type=cv2.NORM_MINMAX
    )

    algo = algorithm.lower()
    if algo == "mantiuk":
        tonemap_op = cv2.createTonemapMantiuk(
            gamma=gamma, scale=contrast, saturation=saturation
        )
    elif algo == "reinhard":
        tonemap_op = cv2.createTonemapReinhard(
            gamma=gamma, intensity=contrast, color_adapt=saturation
        )
    elif algo == "drago":
        bias = max(0.0, min(1.0, 1.0 - contrast / 2))
        tonemap_op = cv2.createTonemapDrago(
            gamma=gamma, saturation=saturation, bias=bias
        )
    else:
        raise ValueError(f"Unknown tonemapping algorithm: {algorithm}")

    ldr = tonemap_op.process(hdr_norm.copy())
    ldr_max = float(ldr.max())
    if ldr_max > 0 and ldr_max < 0.99:
        ldr /= ldr_max
    ldr = np.clip(ldr * brightness, 0.0, 1.0)
    ldr = np.nan_to_num(ldr, nan=0.0, posinf=1.0, neginf=0.0)
    ldr_8bit = np.clip(ldr * 255, 0, 255).astype("uint8")

    enhanced = enhance_image(ldr_8bit, reference_image)
    highlight_mask = ldr_8bit.max(axis=2) >= 250
    enhanced[highlight_mask] = [255, 255, 255]
    return enhanced


def tonemap_mantiuk(
    hdr_image: np.ndarray,
    reference_image: Optional[np.ndarray] = None,
    *,
    saturation: float = 1.0,
    contrast: float = 1.0,
    gamma: float = 1.0,
    brightness: float = 1.0,
) -> np.ndarray:
    """Backward compatible wrapper around :func:`tonemap`."""

    return tonemap(
        hdr_image,
        reference_image,
        algorithm="mantiuk",
        saturation=saturation,
        contrast=contrast,
        gamma=gamma,
        brightness=brightness,
    )


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
