import os
import numpy as np
import find_and_merge_aeb as fa


def test_save_hdr_image(tmp_path):
    hdr = np.random.rand(2, 2, 3).astype(np.float32)
    out = fa.save_hdr_image(hdr, tmp_path, 1)
    assert os.path.exists(out)
