# -*- coding: utf-8 -*-
"""Command line tool to group uploaded images by timestamp and similarity."""

import json
import sys
from datetime import timedelta
import logging

try:
    from .find_and_merge_aeb import (
        group_images_by_similarity,
        find_aeb_images_and_exposure_times_from_list,
    )
except ImportError:  # pragma: no cover
    from find_and_merge_aeb import (
        group_images_by_similarity,
        find_aeb_images_and_exposure_times_from_list,
    )


def main(paths):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Grouping %d images", len(paths))
    aeb_images, _ = find_aeb_images_and_exposure_times_from_list(paths)
    logger.info("Found %d AEB images", len(aeb_images))
    groups = group_images_by_similarity(
        aeb_images,
        time_threshold=timedelta(seconds=0.5),
        hash_percent_threshold=10.0,
    )
    logger.info("Formed %d groups", len(groups))
    json.dump(groups, sys.stdout)


if __name__ == "__main__":
    main(sys.argv[1:])

