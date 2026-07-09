"""圖片壓縮工具（utils/image_compressor.py）的單元測試。"""

import pytest
from PIL import Image

from utils.image_compressor import compress_image


class TestCompressImage:
    """compress_image() 測試。"""

    def test_downscales_large_image_preserving_aspect_ratio(self):
        image = Image.new("RGB", (3000, 1500))
        result = compress_image(image, max_edge=1500)

        assert max(result.size) == 1500
        assert result.width / result.height == pytest.approx(2.0)

    def test_does_not_upscale_small_image(self):
        image = Image.new("RGB", (800, 600))
        result = compress_image(image, max_edge=1500)

        assert result.size == (800, 600)

    def test_converts_rgba_to_rgb(self):
        image = Image.new("RGBA", (100, 100))
        result = compress_image(image)

        assert result.mode == "RGB"

    def test_exact_max_edge_not_resized(self):
        image = Image.new("RGB", (1500, 1000))
        result = compress_image(image, max_edge=1500)

        assert result.size == (1500, 1000)
