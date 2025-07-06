# -*- coding: utf-8 -*-
"""Command line tool to group uploaded images by timestamp and similarity."""

import json
import sys
from datetime import timedelta

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
    aeb_images, _ = find_aeb_images_and_exposure_times_from_list(paths)
    groups = group_images_by_similarity(
        aeb_images, time_threshold=timedelta(seconds=0.5)
    )
    json.dump(groups, sys.stdout)


if __name__ == "__main__":
    main(sys.argv[1:])

