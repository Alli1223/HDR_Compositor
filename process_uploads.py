import sys
import os
import cv2
import numpy as np
from find_and_merge_aeb import (
    find_aeb_images_and_exposure_times_from_list,
    load_images,
    create_hdr,
)

def get_medium_exposure_image(images, exposure_times):
    if not images or not exposure_times:
        return None
    pairs = sorted(zip(exposure_times, images), key=lambda x: x[0])
    _, sorted_images = zip(*pairs)
    return sorted_images[len(sorted_images) // 2]


def enhance_image(img, reference=None):
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
        img = cv2.addWeighted(img.astype(np.float32), 0.7, ref.astype(np.float32), 0.3, 0)
        img = img.astype(np.uint8)
    return img


def tonemap_mantiuk(hdr_image, reference_image=None):
    tonemap = cv2.createTonemapMantiuk()
    tonemap.setSaturation(1.6)
    tonemap.setScale(0.7)
    ldr = tonemap.process(hdr_image.copy())
    ldr_8bit = np.clip(ldr * 255, 0, 255).astype('uint8')
    return enhance_image(ldr_8bit, reference_image)

def main():
    if len(sys.argv) < 3:
        print("Usage: process_uploads.py <image1> [<image2> ...] <output>")
        sys.exit(1)
    *image_paths, output_path = sys.argv[1:]
    aeb_images, exposure_times = find_aeb_images_and_exposure_times_from_list(image_paths)
    if not aeb_images:
        print("No AEB-tagged images found", file=sys.stderr)
        sys.exit(1)
    images = load_images(aeb_images)
    hdr = create_hdr(images, exposure_times)
    ref_image = get_medium_exposure_image(images, exposure_times)
    ldr = tonemap_mantiuk(hdr, ref_image)
    cv2.imwrite(output_path, ldr)
    print(output_path)

if __name__ == "__main__":
    main()
