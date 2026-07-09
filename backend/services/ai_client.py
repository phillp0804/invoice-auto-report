"""AI 廠商選擇。

依 config 的 AI_PROVIDER 設定，回傳 ClaudeClient 或 GeminiClient。
兩者實作相同介面（send_text / send_image），ocr_service 與
classifier_service 只依賴這個共用介面，不需要知道底層實際呼叫哪個廠商。
"""

from config import Settings
from services.claude_client import ClaudeClient
from services.gemini_client import GeminiClient

AiClient = ClaudeClient | GeminiClient


def create_ai_client(settings: Settings) -> AiClient:
    """依 settings.ai_provider 建立對應的 AI 客戶端。

    Args:
        settings: 應用程式設定（get_settings() 的回傳值）。

    Returns:
        ClaudeClient 或 GeminiClient 實例。

    Raises:
        ValueError: ai_provider 不是 "claude" 或 "gemini"。
    """
    if settings.ai_provider == "gemini":
        return GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if settings.ai_provider == "claude":
        return ClaudeClient(api_key=settings.anthropic_api_key)

    raise ValueError(
        f"不支援的 AI_PROVIDER：{settings.ai_provider}，須為 claude 或 gemini"
    )
