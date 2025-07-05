import subprocess
from unittest import mock
import find_and_merge_aeb as fa


def fake_run(cmd, shell, stdout, text):
    class R:
        def __init__(self, out):
            self.stdout = out
    if "XPKeywords" in cmd:
        img = cmd.split('"')[1]
        return R("AEB" if img.endswith('1.jpg') else 'aeb')
    if "ExposureTime" in cmd:
        img = cmd.split('"')[1]
        return R("1/2" if img.endswith('1.jpg') else "0.25")
    return R("")


@mock.patch.object(subprocess, "run", side_effect=fake_run)
def test_find_aeb_images_and_exposure_times_from_list(mock_run):
    images = ["1.jpg", "2.jpg"]
    aeb, times = fa.find_aeb_images_and_exposure_times_from_list(images)
    assert aeb == images
    assert times == [0.5, 0.25]
