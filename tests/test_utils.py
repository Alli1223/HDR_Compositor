import numpy as np
from hdr_utils import tonemap_mantiuk


def test_tonemap_mantiuk_output_properties():
    hdr = np.random.rand(2, 2, 3).astype(np.float32) * 2.0
    ldr = tonemap_mantiuk(hdr)
    assert ldr.shape == hdr.shape
    assert ldr.dtype == np.uint8
    assert ldr.min() >= 0 and ldr.max() <= 255
