"""圖片壓縮工具。

純函式，無外部依賴，供 ocr_service（送 AI 辨識前）與
storage_service（存本機備份前）共用，避免重複實作。
"""

from PIL import Image


def compress_image(image: Image.Image, max_edge: int = 1500) -> Image.Image:
    """壓縮圖片至指定最長邊，降低檔案大小。

    Args:
        image: 原始 PIL Image。
        max_edge: 最長邊像素上限（預設 1500px）。

    Returns:
        壓縮後的 PIL Image（RGB 模式，最長邊不超過 max_edge，不放大原圖）。
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    longest_edge = max(image.size)
    if longest_edge > max_edge:
        scale = max_edge / longest_edge
        new_size = (round(image.width * scale), round(image.height * scale))
        image = image.resize(new_size, Image.LANCZOS)

    return image
