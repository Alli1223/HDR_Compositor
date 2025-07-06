import sys
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT.parent))

from HDR_Compositor.find_and_merge_aeb import group_images_by_datetime
import HDR_Compositor.find_and_merge_aeb as find_and_merge_aeb


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


def test_group_images_half_second(monkeypatch):
    dates = {
        "a.jpg": datetime.datetime(2023, 1, 1, 13, 0, 0),
        "b.jpg": datetime.datetime(2023, 1, 1, 13, 0, 0, 400000),
        "c.jpg": datetime.datetime(2023, 1, 1, 13, 0, 1),
    }

    monkeypatch.setattr(find_and_merge_aeb, "extract_datetime", lambda p: dates[p])

    groups = group_images_by_datetime(list(dates.keys()), threshold=datetime.timedelta(seconds=0.5))
    assert groups == [["a.jpg", "b.jpg"], ["c.jpg"]]
