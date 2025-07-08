import sys
from pathlib import Path
import subprocess
import datetime
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT.parent))

from HDR_Compositor.find_and_merge_aeb import (
    group_images_by_datetime,
    find_aeb_images_and_exposure_times_from_list,
)
from HDR_Compositor.hdr_utils import align_images, remove_ghosts


def test_align_remove_empty():
    assert align_images([]) == []
    assert remove_ghosts([]) == []


def test_group_images_missing_datetime(monkeypatch):
    monkeypatch.setattr(
        'HDR_Compositor.find_and_merge_aeb.extract_datetime',
        lambda p: None,
    )
    groups = group_images_by_datetime(['a.jpg', 'b.jpg'])
    assert groups == []


def test_find_aeb_images_and_exposure_times(monkeypatch):
    def fake_run(cmd, stdout=None, text=None):
        assert cmd[0] == 'exiftool'
        class R:
            def __init__(self, out):
                self.stdout = out
        data = [
            {"SourceFile": "img1.jpg", "XPKeywords": "AEB", "ExposureTime": "1/60"},
            {"SourceFile": "img2.jpg", "XPKeywords": "", "ExposureTime": "1/60"},
        ]
        return R(json.dumps(data))

    monkeypatch.setattr(subprocess, 'run', fake_run)
    images, times = find_aeb_images_and_exposure_times_from_list(['img1.jpg', 'img2.jpg'])
    assert images == ['img1.jpg']
    assert times == [1/60]

