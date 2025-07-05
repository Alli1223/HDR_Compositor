import sys
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from find_and_merge_aeb import group_images_by_datetime
import find_and_merge_aeb


def test_group_images_by_datetime(monkeypatch):
    dates = {
        "img1.jpg": datetime.datetime(2023, 1, 1, 12, 0, 0),
        "img2.jpg": datetime.datetime(2023, 1, 1, 12, 0, 1),
        "img3.jpg": datetime.datetime(2023, 1, 1, 12, 0, 4),
        "img4.jpg": datetime.datetime(2023, 1, 1, 12, 0, 6),
    }

    def fake_extract(path):
        return dates[path]

    monkeypatch.setattr(find_and_merge_aeb, "extract_datetime", fake_extract)

    groups = group_images_by_datetime(list(dates.keys()), threshold=datetime.timedelta(seconds=2))
    assert groups == [["img1.jpg", "img2.jpg"], ["img3.jpg", "img4.jpg"]]
