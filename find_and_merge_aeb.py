import os
import subprocess
import sys
import cv2
import numpy as np
from datetime import datetime, timedelta
from hdr_utils import tonemap_mantiuk

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

def create_hdr(images, exposure_times):
    # Convert exposure times to the format expected by OpenCV (numpy array)
    times = np.array(exposure_times, dtype=np.float32)

    # Existing HDR creation code, now including `times` in the `process` call
    merge_debevec = cv2.createMergeDebevec()
    hdr = merge_debevec.process(images, times=times)
    return hdr


def save_hdr_image(hdr_image, save_path, group_index):
    """Tonemap and save an HDR image."""
    output_path = os.path.join(save_path, f"hdr_image_{group_index}_mantiuk.jpg")
    ldr = tonemap_mantiuk(hdr_image)
    cv2.imwrite(output_path, ldr)
    return output_path


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
            output_path = save_hdr_image(hdr_image, output_dir, group_index)
            print(f"Group {group_index}: HDR image saved to {output_path}")
        else:
            print(f"Group {group_index}: Failed to load images or exposure times are missing.")