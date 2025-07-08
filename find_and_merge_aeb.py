import os
import json
import subprocess
import sys
import cv2
import numpy as np
import warnings
from datetime import datetime, timedelta
from typing import Iterable, List, Tuple

try:  # support running as a script or a package module
    from .hdr_utils import (
        get_medium_exposure_image,
        enhance_image,
        align_images,
        remove_ghosts,
    )
except ImportError:  # pragma: no cover - fallback for direct execution
    from hdr_utils import (
        get_medium_exposure_image,
        enhance_image,
        align_images,
        remove_ghosts,
    )


def _run_exiftool_json(paths: Iterable[str], tags: Iterable[str]) -> list:
    """Return exif data for *paths* as parsed JSON."""
    if not paths:
        return []
    cmd = [
        "exiftool",
        "-json",
        *[f"-{t}" for t in tags],
        *paths,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def find_aeb_images(directory: str) -> List[str]:
    """Return all image files in *directory* tagged with 'AEB'."""
    image_files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff"))
    ]
    data = _run_exiftool_json(image_files, ["XPKeywords"])
    keywords = {d.get("SourceFile"): str(d.get("XPKeywords", "")) for d in data}
    return [p for p in image_files if "aeb" in keywords.get(p, "").lower()]


def extract_datetime(image_path):
    cmd = f'exiftool -DateTimeOriginal -d "%Y:%m:%d %H:%M:%S" "{image_path}"'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
    datetime_str = ""
    for line in result.stdout.split("\n"):
        if "Date/Time Original" in line:
            datetime_str = line.split(": ", 1)[1]
            break
    try:
        return datetime.strptime(datetime_str.strip(), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def group_images_by_datetime(image_paths, threshold=timedelta(seconds=2)):
    grouped_images = []
    for path in image_paths:
        dt = extract_datetime(path)
        if not dt:
            continue  # Skip images where datetime couldn't be extracted
        if not grouped_images or (dt - grouped_images[-1][1] > threshold):
            grouped_images.append(([path], dt))
        else:
            grouped_images[-1][0].append(path)
    return [group for group, _ in grouped_images]


def _parse_exposure(value: str) -> Tuple[bool, float]:
    """Return (success, exposure_value) parsed from a string."""
    value = value.strip()
    try:
        return True, float(value)
    except ValueError:
        pass
    if "/" in value:
        try:
            num, den = value.split("/")
            return True, float(num) / float(den)
        except ValueError:
            pass
    return False, 0.0


def find_aeb_images_and_exposure_times_from_list(image_paths: Iterable[str]) -> Tuple[List[str], List[float]]:
    """Return AEB-tagged paths and their exposure times for the given list."""
    meta = _run_exiftool_json(image_paths, ["XPKeywords", "ExposureTime"])
    aeb_images: List[str] = []
    exposure_times: List[float] = []
    for entry in meta:
        path = entry.get("SourceFile")
        if path is None:
            continue
        keywords = str(entry.get("XPKeywords", "")).lower()
        if "aeb" not in keywords:
            continue
        ok, value = _parse_exposure(str(entry.get("ExposureTime", "")))
        if ok:
            aeb_images.append(path)
            exposure_times.append(value)
        else:
            print(
                f"Warning: Could not parse exposure time for image {os.path.basename(path)} with value '{entry.get('ExposureTime', '')}'. Skipping this image."
            )
    return aeb_images, exposure_times


def load_images(image_paths):
    images = []
    for path in image_paths:
        img = cv2.imread(path)
        images.append(img)
    return images


def create_hdr(
    images,
    exposure_times,
    align: bool = False,
    deghost: bool = False,
):
    """Create an HDR image with optional alignment and deghosting.

    The function validates the inputs and raises ``ValueError`` when the
    provided lists do not match the expected lengths or contain invalid
    values. ``warnings.warn`` is used when alignment or deghosting is
    requested for a single image."""

    if not images:
        raise ValueError("No images provided for HDR merge")

    if len(images) != len(exposure_times):
        raise ValueError("Number of exposure times must match number of images")

    if any(t <= 0 for t in exposure_times):
        raise ValueError("Exposure times must be positive values")

    if (align or deghost) and len(images) < 2:
        warnings.warn("Alignment or deghosting requested with a single image; ignoring")

    proc_images = images
    if align and len(images) > 1:
        proc_images = align_images(proc_images)
    if deghost and len(images) > 1:
        proc_images = remove_ghosts(proc_images)

    times = np.asarray(exposure_times, dtype=np.float32)
    merge_debevec = cv2.createMergeDebevec()
    hdr = merge_debevec.process(proc_images, times=times)
    return hdr


def save_hdr_image(hdr_image, save_path, group_index, images=None, exposure_times=None):
    tonemapMantiuk = cv2.createTonemapMantiuk()
    tonemapMantiuk.setSaturation(1.0)
    tonemapMantiuk.setScale(1.0)
    ldr = tonemapMantiuk.process(hdr_image.copy())
    ldr_8bit = np.clip(ldr * 255, 0, 255).astype("uint8")

    ref = (
        get_medium_exposure_image(images, exposure_times)
        if images and exposure_times
        else None
    )
    enhanced = enhance_image(ldr_8bit, ref)

    output_path = os.path.join(save_path, f"hdr_image_{group_index}_mantiuk.jpg")
    cv2.imwrite(output_path, enhanced)


if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("INPUT_DIR")
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("OUTPUT_DIR")

    all_image_paths = find_aeb_images(
        input_dir
    )  # Assume this returns all AEB image paths
    grouped_image_paths = group_images_by_datetime(all_image_paths)

    for group_index, image_group in enumerate(grouped_image_paths, start=1):
        aeb_images, exposure_times = find_aeb_images_and_exposure_times_from_list(
            image_group
        )
        if not aeb_images:
            print(f"No AEB-tagged images found in group {group_index}.")
            continue

        images = load_images(aeb_images)
        if images:
            hdr_image = create_hdr(images, exposure_times)
            save_hdr_image(hdr_image, output_dir, group_index, images, exposure_times)
            print(
                f"Group {group_index}: HDR image saved to {output_dir}/hdr_image_{group_index}.jpg"
            )
        else:
            print(
                f"Group {group_index}: Failed to load images or exposure times are missing."
            )
