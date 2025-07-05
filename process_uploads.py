import sys
import os
import cv2
import numpy as np
import argparse
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
    parser = argparse.ArgumentParser(description="Process uploaded images")
    parser.add_argument("paths", nargs="+", help="input images followed by output path")
    parser.add_argument("--align", action="store_true", help="auto align images")
    parser.add_argument("--deghost", action="store_true", help="apply anti-ghosting")
    parser.add_argument("--contrast", type=float, default=0.7, help="tone mapping contrast scale")
    parser.add_argument("--saturation", type=float, default=1.6, help="tone mapping saturation")
    args = parser.parse_args()

    if len(args.paths) < 2:
        print("Usage: process_uploads.py [--align] [--deghost] <image1> [<image2> ...] <output>")
        sys.exit(1)

    *image_paths, output_path = args.paths
    aeb_images, exposure_times = find_aeb_images_and_exposure_times_from_list(image_paths)
    if not aeb_images:
        print("No AEB-tagged images found", file=sys.stderr)
        sys.exit(1)
    images = load_images(aeb_images)
    hdr = create_hdr(images, exposure_times, align=args.align, deghost=args.deghost)
    ref_image = get_medium_exposure_image(images, exposure_times)
    ldr = tonemap_mantiuk(
        hdr,
        ref_image,
        saturation=args.saturation,
        contrast=args.contrast,
    )
    cv2.imwrite(output_path, ldr)
    print(output_path)

if __name__ == "__main__":
    main()
