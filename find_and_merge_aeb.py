import os
import subprocess
import sys
import cv2
import numpy as np
from datetime import datetime, timedelta
import logging
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

def find_aeb_images(directory):
    aeb_images = []
    # List all image files in the directory
    image_files = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
    for image_file in image_files:
        image_path = os.path.join(directory, image_file)
        # Use exiftool to get XP Keywords tag for the image
        cmd = f'exiftool -XPKeywords "{image_path}"'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
        if 'aeb' in result.stdout.lower():
            aeb_images.append(image_path)
    return aeb_images

def extract_datetime(image_path):
    """Return the image capture time or fall back to the file modification time."""
    cmd = f'exiftool -DateTimeOriginal -d "%Y:%m:%d %H:%M:%S" "{image_path}"'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
    datetime_str = ""
    for line in result.stdout.split("\n"):
        if "Date/Time Original" in line:
            datetime_str = line.split(": ", 1)[1]
            break
    if datetime_str:
        try:
            return datetime.strptime(datetime_str.strip(), "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass
    try:
        timestamp = os.path.getmtime(image_path)
        return datetime.fromtimestamp(timestamp)
    except Exception:
        return None

def group_images_by_datetime(image_paths, threshold=timedelta(seconds=2)):
    grouped_images = []
    for path in image_paths:
        dt = extract_datetime(path)
        if not dt:
            continue
        if not grouped_images or (dt - grouped_images[-1][1] > threshold):
            grouped_images.append(([path], dt))
        else:
            grouped_images[-1][0].append(path)
    return [group for group, _ in grouped_images]

def image_hash(img: np.ndarray, size: int = 8) -> np.ndarray:
    """Return a simple average hash for the given image."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    avg = resized.mean()
    return (resized > avg).astype(np.uint8).flatten()


def _hash_to_hex(h: np.ndarray) -> str:
    """Return a hexadecimal string representation of a binary hash."""
    bits = ''.join('1' if b else '0' for b in h)
    return f"{int(bits, 2):0{len(h) // 4}x}"


def group_images_by_hash(
    image_paths,
    *,
    hash_percent_threshold: float = 10.0,
):
    """Group images purely by perceptual hash similarity.

    All images are hashed first and then clustered such that any two images
    differing by ``hash_percent_threshold`` percent or less end up in the same
    group.  Groups are discovered by treating images with small hash distances as
    connected components in a graph.
    """

    logger = logging.getLogger(__name__)
    logger.info("Grouping %d images by hash", len(image_paths))

    items = []
    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            continue
        h = image_hash(img)
        logger.info("Hash for %s: %s", path, _hash_to_hex(h))
        items.append((path, h))

    # Log pairwise similarities
    for i, (p1, h1) in enumerate(items):
        for p2, h2 in [items[j] for j in range(i + 1, len(items))]:
            distance = np.count_nonzero(h1 != h2)
            diff_percent = distance / len(h1) * 100
            logger.info(
                "Similarity %s vs %s: %.2f%% (%d/%d)",
                p1,
                p2,
                diff_percent,
                distance,
                len(h1),
            )

    # Build groups using connected components based on hash distance
    n = len(items)
    visited = [False] * n
    groups = []

    for i in range(n):
        if visited[i]:
            continue
        stack = [i]
        visited[i] = True
        group = []
        while stack:
            idx = stack.pop()
            path_i, hash_i = items[idx]
            group.append(path_i)
            for j in range(n):
                if visited[j]:
                    continue
                path_j, hash_j = items[j]
                distance = np.count_nonzero(hash_i != hash_j)
                diff_percent = distance / len(hash_i) * 100
                if diff_percent <= hash_percent_threshold:
                    visited[j] = True
                    stack.append(j)
        groups.append(group)

    logger.info("Formed %d groups", len(groups))
    for i, g in enumerate(groups, 1):
        logger.info("Group %d: %s", i, g)

    return groups

def get_exposure_times_from_list(image_paths):
    """Return exposure times for the given image paths."""
    valid_paths = []
    exposure_times = []
    for image_path in image_paths:
        cmd = f'exiftool -ExposureTime -b "{image_path}"'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
        exposure_time_str = result.stdout.strip()
        if not exposure_time_str:
            print(
                f"Warning: Missing exposure time for image {os.path.basename(image_path)}. Skipping this image."
            )
            continue
        try:
            exposure_time = float(exposure_time_str)
        except ValueError:
            try:
                numerator, denominator = exposure_time_str.split('/')
                exposure_time = float(numerator) / float(denominator)
            except ValueError:
                print(
                    f"Warning: Could not parse exposure time for image {os.path.basename(image_path)} with value '{exposure_time_str}'. Skipping this image."
                )
                continue
        valid_paths.append(image_path)
        exposure_times.append(exposure_time)
    return valid_paths, exposure_times

def find_aeb_images_and_exposure_times_from_list(image_paths):
    aeb_images = []
    exposure_times = []
    for image_path in image_paths:
        # Check for 'aeb' in XP Keywords
        keywords_cmd = f'exiftool -XPKeywords "{image_path}"'
        keywords_result = subprocess.run(keywords_cmd, shell=True, stdout=subprocess.PIPE, text=True)
        if 'aeb' in keywords_result.stdout.lower():
            aeb_images.append(image_path)
            # Extract exposure time
            exposure_cmd = f'exiftool -ExposureTime -b "{image_path}"'
            exposure_result = subprocess.run(exposure_cmd, shell=True, stdout=subprocess.PIPE, text=True)
            exposure_time_str = exposure_result.stdout.strip()
            try:
                # Attempt to parse the exposure time as a float directly
                exposure_time = float(exposure_time_str)
            except ValueError:
                try:
                    # Attempt to parse fractional exposure time (e.g., "1/250")
                    numerator, denominator = exposure_time_str.split('/')
                    exposure_time = float(numerator) / float(denominator)
                except ValueError:
                    # Handle images without a valid exposure time or where parsing fails
                    print(f"Warning: Could not parse exposure time for image {os.path.basename(image_path)} with value '{exposure_time_str}'. Skipping this image.")
                    aeb_images.pop()  # Remove the last image added since it has no valid exposure time
                    continue  # Skip further processing for this image
            exposure_times.append(exposure_time)
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
    """Create an HDR image with optional alignment and deghosting."""
    proc_images = images
    if align:
        proc_images = align_images(proc_images)
    if deghost:
        proc_images = remove_ghosts(proc_images)

    times = np.array(exposure_times, dtype=np.float32)
    merge_debevec = cv2.createMergeDebevec()
    hdr = merge_debevec.process(proc_images, times=times)
    return hdr


def save_hdr_image(hdr_image, save_path, group_index, images=None, exposure_times=None):
    tonemapMantiuk = cv2.createTonemapMantiuk()
    tonemapMantiuk.setSaturation(1.0)
    tonemapMantiuk.setScale(1.0)
    ldr = tonemapMantiuk.process(hdr_image.copy())
    ldr_8bit = np.clip(ldr * 255, 0, 255).astype('uint8')

    ref = get_medium_exposure_image(images, exposure_times) if images and exposure_times else None
    enhanced = enhance_image(ldr_8bit, ref)

    output_path = os.path.join(save_path, f"hdr_image_{group_index}_mantiuk.jpg")
    cv2.imwrite(output_path, enhanced)


if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("INPUT_DIR")
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("OUTPUT_DIR")

    all_image_paths = find_aeb_images(input_dir)  # Assume this returns all AEB image paths
    grouped_image_paths = group_images_by_datetime(all_image_paths)

    for group_index, image_group in enumerate(grouped_image_paths, start=1):
        aeb_images, exposure_times = find_aeb_images_and_exposure_times_from_list(image_group)
        if not aeb_images:
            print(f"No AEB-tagged images found in group {group_index}.")
            continue

        images = load_images(aeb_images)
        if images:
            hdr_image = create_hdr(images, exposure_times)
            save_hdr_image(hdr_image, output_dir, group_index, images, exposure_times)
            print(f"Group {group_index}: HDR image saved to {output_dir}/hdr_image_{group_index}.jpg")
        else:
            print(f"Group {group_index}: Failed to load images or exposure times are missing.")
