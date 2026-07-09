"""發票圖片備份儲存服務（storage_service）的單元測試。"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from services.storage_service import build_invoice_filename, save_invoice_image


class TestBuildInvoiceFilename:
    """build_invoice_filename() 測試。"""

    def test_uses_invoice_date_when_available(self):
        result = build_invoice_filename("王小明", "AB12345678", date(2024, 7, 8))

        assert result == "王小明_20240708_AB12345678"

    def test_falls_back_to_fallback_date_when_invoice_date_missing(self):
        result = build_invoice_filename(
            "王小明", "AB12345678", None, fallback_date=date(2024, 7, 9)
        )

        assert result == "王小明_20240709_AB12345678"

    def test_sanitizes_path_traversal_characters_in_name(self):
        result = build_invoice_filename(
            "../../etc/passwd", "AB12345678", date(2024, 7, 8)
        )

        assert "/" not in result
        assert ".." not in result

    def test_sanitizes_whitespace_in_name(self):
        result = build_invoice_filename("王 小明", "AB12345678", date(2024, 7, 8))

        assert result == "王_小明_20240708_AB12345678"


class TestSaveInvoiceImage:
    """save_invoice_image() 測試。"""

    def test_saves_compressed_jpeg_and_returns_relative_path(self, tmp_path):
        fake_settings = SimpleNamespace(upload_dir=str(tmp_path))
        with patch("services.storage_service.get_settings", return_value=fake_settings):
            image = Image.new("RGB", (3000, 1500))
            relative_path = save_invoice_image(image, "王小明_20240708_AB12345678")

        saved_path = tmp_path / "王小明_20240708_AB12345678.jpg"
        assert saved_path.exists()
        assert relative_path.endswith("王小明_20240708_AB12345678.jpg")

        with Image.open(saved_path) as saved_image:
            assert max(saved_image.size) <= 1500

    def test_avoids_overwriting_existing_file(self, tmp_path):
        fake_settings = SimpleNamespace(upload_dir=str(tmp_path))
        with patch("services.storage_service.get_settings", return_value=fake_settings):
            image = Image.new("RGB", (500, 500))
            first_path = save_invoice_image(image, "王小明_20240708_AB12345678")
            second_path = save_invoice_image(image, "王小明_20240708_AB12345678")

        assert first_path != second_path
        assert (tmp_path / "王小明_20240708_AB12345678.jpg").exists()
        assert (tmp_path / "王小明_20240708_AB12345678_2.jpg").exists()

    def test_creates_upload_dir_if_missing(self, tmp_path):
        nested_dir = tmp_path / "nested" / "uploads"
        fake_settings = SimpleNamespace(upload_dir=str(nested_dir))
        with patch("services.storage_service.get_settings", return_value=fake_settings):
            image = Image.new("RGB", (100, 100))
            save_invoice_image(image, "test")

        assert nested_dir.exists()
