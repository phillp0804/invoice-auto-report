"""AI 客戶端共用例外類型。"""


class AiQuotaExceededError(RuntimeError):
    """AI API 額度或速率限制已達上限（例如 429 Too Many Requests）。

    獨立於一般 RuntimeError，讓呼叫端（invoice_router）可以辨別出
    「額度用完」這種可預期、可提示使用者稍後再試的情況，
    跟其他非預期的 AI 服務錯誤分開處理、回傳不同的錯誤訊息。
    """
