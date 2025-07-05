import sys
import os
import cv2
import numpy as np
try:  # allow usage both as script and module
    from .find_and_merge_aeb import (
        find_aeb_images_and_exposure_times_from_list,
        load_images,
        create_hdr,
    )
    from .hdr_utils import get_medium_exposure_image, tonemap_mantiuk
except ImportError:  # pragma: no cover - fallback for direct execution
    from find_and_merge_aeb import (
        find_aeb_images_and_exposure_times_from_list,
        load_images,
        create_hdr,
    )
    from hdr_utils import get_medium_exposure_image, tonemap_mantiuk

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
