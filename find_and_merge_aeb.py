import os
import subprocess
import sys
import cv2
import numpy as np
from datetime import datetime, timedelta
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
        cmd = ["exiftool", "-XPKeywords", image_path]
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error running exiftool for {image_path}: {e}", file=sys.stderr)
            continue
        if 'aeb' in result.stdout.lower():
            aeb_images.append(image_path)
    return aeb_images

def extract_datetime(image_path):
    cmd = [
        "exiftool",
        "-DateTimeOriginal",
        "-d",
        "%Y:%m:%d %H:%M:%S",
        image_path,
    ]
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error running exiftool for {image_path}: {e}", file=sys.stderr)
        return None
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

def find_aeb_images_and_exposure_times_from_list(image_paths):
    aeb_images = []
    exposure_times = []
    for image_path in image_paths:
        # Check for 'aeb' in XP Keywords
        keywords_cmd = ["exiftool", "-XPKeywords", image_path]
        try:
            keywords_result = subprocess.run(
                keywords_cmd, check=True, stdout=subprocess.PIPE, text=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error running exiftool for {image_path}: {e}", file=sys.stderr)
            continue
        if 'aeb' in keywords_result.stdout.lower():
            aeb_images.append(image_path)
            # Extract exposure time
            exposure_cmd = ["exiftool", "-ExposureTime", "-b", image_path]
            try:
                exposure_result = subprocess.run(
                    exposure_cmd, check=True, stdout=subprocess.PIPE, text=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(
                    f"Error running exiftool for {image_path}: {e}",
                    file=sys.stderr,
                )
                aeb_images.pop()
                continue
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
        if img is not None:
            images.append(img)
        else:
            print(f"Warning: could not read {path}", file=sys.stderr)
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
