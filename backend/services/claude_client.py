"""Claude API 共用客戶端。

統一管理 API Key 讀取、錯誤處理、重試機制，
供 ocr_service 和 classifier_service 共用。

介面（send_text / send_image）與 services/gemini_client.py 一致，
兩者可透過 services/ai_client.py 依 AI_PROVIDER 設定互換使用。
"""

import base64

import anthropic

from services.ai_errors import AiQuotaExceededError

# 統一在此處指定模型，避免各 service 各自寫死不同版本
_MODEL = "claude-opus-4-8"

# SDK 內建重試機制涵蓋 408/409/429/5xx 與連線錯誤（指數退避）
_MAX_RETRIES = 2


class ClaudeClient:
    """Claude API 底層呼叫客戶端。"""

    def __init__(self, api_key: str):
        """初始化 Claude API 客戶端。

        Args:
            api_key: Anthropic API 金鑰。
        """
        self._client = anthropic.Anthropic(api_key=api_key, max_retries=_MAX_RETRIES)

    def send_text(self, system_prompt: str, user_text: str, max_tokens: int = 1024) -> str:
        """發送純文字訊息至 Claude API（供 classifier_service 使用）。

        Args:
            system_prompt: 系統層級 prompt。
            user_text: 使用者文字內容。
            max_tokens: 最大回傳 token 數。

        Returns:
            Claude 回傳的文字內容。
        """
        return self._send(system_prompt, [{"type": "text", "text": user_text}], max_tokens)

    def send_image(
        self,
        system_prompt: str,
        image_bytes: bytes,
        media_type: str,
        user_text: str,
        max_tokens: int = 1024,
    ) -> str:
        """發送圖片＋文字訊息至 Claude Vision（供 ocr_service 使用）。

        Args:
            system_prompt: 系統層級 prompt。
            image_bytes: 圖片二進位內容。
            media_type: 圖片 MIME type（例如 "image/jpeg"）。
            user_text: 附加的使用者文字內容。
            max_tokens: 最大回傳 token 數。

        Returns:
            Claude 回傳的文字內容。
        """
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": image_b64},
            },
            {"type": "text", "text": user_text},
        ]
        return self._send(system_prompt, content, max_tokens)

    def _send(self, system_prompt: str, content: list, max_tokens: int) -> str:
        """呼叫 Claude API 並合併回傳的所有 text 區塊。

        Raises:
            AiQuotaExceededError: 額度或速率限制已達上限（429，SDK 重試後仍失敗）。
            RuntimeError: 其他 Claude API 呼叫失敗（例如認證錯誤、伺服器錯誤等）。
        """
        try:
            response = self._client.messages.create(
                model=_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.RateLimitError as exc:
            raise AiQuotaExceededError(f"Claude API 額度已用完：{exc}") from exc
        except anthropic.APIError as exc:
            raise RuntimeError(f"Claude API 呼叫失敗：{exc}") from exc

        return "".join(
            block.text for block in response.content if block.type == "text"
        )
