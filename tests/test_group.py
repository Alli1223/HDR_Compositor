from datetime import datetime, timedelta
from unittest import mock
import find_and_merge_aeb as fa


def test_group_images_by_datetime():
    paths = ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"]
    times = [
        datetime(2024, 1, 1, 0, 0, 0),
        datetime(2024, 1, 1, 0, 0, 1),
        datetime(2024, 1, 1, 0, 0, 10),
        datetime(2024, 1, 1, 0, 0, 11),
    ]

    def fake_extract(path):
        return times[paths.index(path)]

    with mock.patch.object(fa, "extract_datetime", side_effect=fake_extract):
        groups = fa.group_images_by_datetime(paths, threshold=timedelta(seconds=2))

    assert groups == [["img1.jpg", "img2.jpg"], ["img3.jpg", "img4.jpg"]]
