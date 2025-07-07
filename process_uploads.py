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
    from .hdr_utils import get_medium_exposure_image, tonemap
except ImportError:  # pragma: no cover - fallback for direct execution
    from find_and_merge_aeb import (
        find_aeb_images_and_exposure_times_from_list,
        load_images,
        create_hdr,
    )
    from hdr_utils import get_medium_exposure_image, tonemap

def main():
    parser = argparse.ArgumentParser(description="Process uploaded images")
    parser.add_argument("paths", nargs="+", help="input images followed by output path")
    parser.add_argument("--align", action="store_true", help="auto align images")
    parser.add_argument("--deghost", action="store_true", help="apply anti-ghosting")
    parser.add_argument("--contrast", type=float, default=1.0, help="tone mapping contrast scale")
    parser.add_argument("--saturation", type=float, default=1.0, help="tone mapping saturation")
    parser.add_argument("--gamma", type=float, default=1.0, help="tone mapping gamma")
    parser.add_argument("--brightness", type=float, default=1.0, help="output brightness scale")
    parser.add_argument(
        "--algorithm",
        choices=["mantiuk", "reinhard", "drago"],
        default="mantiuk",
        help="tone mapping algorithm",
    )
    args = parser.parse_args()

    if len(args.paths) < 2:
        print("Usage: process_uploads.py [--align] [--deghost] <image1> [<image2> ...] <output>")
        sys.exit(1)

    *image_paths, output_path = args.paths
    aeb_images, exposure_times = find_aeb_images_and_exposure_times_from_list(image_paths)
    if not aeb_images:
        print("No AEB-tagged images found", file=sys.stderr)
        sys.exit(1)

    def progress(pct: int):
        print(f"PROGRESS {pct}", flush=True)

    progress(10)
    images = load_images(aeb_images)
    progress(40)
    hdr = create_hdr(images, exposure_times, align=args.align, deghost=args.deghost)
    progress(70)
    ref_image = get_medium_exposure_image(images, exposure_times)
    ldr = tonemap(
        hdr,
        ref_image,
        algorithm=args.algorithm,
        saturation=args.saturation,
        contrast=args.contrast,
        gamma=args.gamma,
        brightness=args.brightness,
    )
    progress(90)
    cv2.imwrite(output_path, ldr)
    progress(100)
    print(output_path)

if __name__ == "__main__":
    main()
