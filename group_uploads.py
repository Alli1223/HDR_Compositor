# -*- coding: utf-8 -*-
"""Command line tool to group uploaded images by perceptual hash similarity."""

import json
import sys
import logging
import os
from contextlib import redirect_stdout
import io

try:
    from .find_and_merge_aeb import (
        group_images_by_hash,
        find_aeb_images_and_exposure_times_from_list,
    )
except ImportError:  # pragma: no cover
    from find_and_merge_aeb import (
        group_images_by_hash,
        find_aeb_images_and_exposure_times_from_list,
    )


def main(paths):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Grouping %d images", len(paths))

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            aeb_images, _ = find_aeb_images_and_exposure_times_from_list(paths)
    except Exception as exc:  # pragma: no cover - if exiftool missing
        logger.warning("AEB detection failed: %s", exc)
        aeb_images = paths
    else:
        warnings = buf.getvalue().strip()
        if warnings:
            for line in warnings.splitlines():
                logger.warning(line)

    if not aeb_images:
        logger.info("No AEB images found, proceeding with all images")
        aeb_images = paths

    groups = group_images_by_hash(aeb_images, hash_percent_threshold=10.0)
    logger.info("Formed %d groups", len(groups))

    groups_names = [[os.path.basename(p) for p in g] for g in groups]
    json.dump(groups_names, sys.stdout)


if __name__ == "__main__":
    main(sys.argv[1:])

