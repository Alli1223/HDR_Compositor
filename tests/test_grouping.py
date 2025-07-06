import sys
from pathlib import Path
import datetime
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT.parent))

from HDR_Compositor.find_and_merge_aeb import (
    group_images_by_datetime,
    group_images_by_similarity,
)
import HDR_Compositor.group_uploads as group_uploads
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


def test_group_images_similarity(monkeypatch):
    dates = {
        "a.jpg": datetime.datetime(2023, 1, 1, 13, 0, 0),
        "b.jpg": datetime.datetime(2023, 1, 1, 13, 0, 0, 100000),
        "c.jpg": datetime.datetime(2023, 1, 1, 13, 0, 0, 200000),
    }

    images = {
        "a.jpg": np.zeros((5, 5, 3), dtype=np.uint8),
        "b.jpg": np.zeros((5, 5, 3), dtype=np.uint8) + 5,
        "c.jpg": np.full((5, 5, 3), 255, dtype=np.uint8),
    }

    monkeypatch.setattr(find_and_merge_aeb, "extract_datetime", lambda p: dates[p])
    monkeypatch.setattr(find_and_merge_aeb.cv2, "imread", lambda p: images[p])

    groups = group_images_by_similarity(
        list(dates.keys()),
        time_threshold=datetime.timedelta(seconds=0.5),
        similarity_threshold=30,
    )
    assert groups == [["a.jpg", "b.jpg"], ["c.jpg"]]


def test_group_uploads_main(monkeypatch, capsys):
    monkeypatch.setattr(
        group_uploads, "find_aeb_images_and_exposure_times_from_list", lambda p: (p, [])
    )
    monkeypatch.setattr(
        group_uploads, "group_images_by_similarity", lambda p, time_threshold=None: [p]
    )
    group_uploads.main(["x.jpg", "y.jpg"])
    out = capsys.readouterr().out.strip()
    assert out == '[["x.jpg", "y.jpg"]]'
