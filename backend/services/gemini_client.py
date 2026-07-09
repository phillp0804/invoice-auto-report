"""Gemini API 共用客戶端。

統一管理 API Key 讀取與錯誤處理，供 ocr_service 和 classifier_service 共用。

介面（send_text / send_image）與 services/claude_client.py 一致，
兩者可透過 services/ai_client.py 依 AI_PROVIDER 設定互換使用，
讓專案可以在 Claude 與 Gemini 之間切換而不需要更動 service 層邏輯。
"""

from google import genai
from google.genai import errors as genai_errors
from google.genai import types


class GeminiClient:
    """Gemini API 底層呼叫客戶端。"""

    def __init__(self, api_key: str, model: str):
        """初始化 Gemini API 客戶端。

        Args:
            api_key: Gemini API 金鑰。
            model: 使用的 Gemini 模型名稱（例如 "gemini-2.5-flash"）。
        """
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def send_text(self, system_prompt: str, user_text: str, max_tokens: int = 1024) -> str:
        """發送純文字訊息至 Gemini API（供 classifier_service 使用）。

        Args:
            system_prompt: 系統層級 prompt。
            user_text: 使用者文字內容。
            max_tokens: 最大回傳 token 數。

        Returns:
            Gemini 回傳的文字內容。
        """
        return self._send(system_prompt, [user_text], max_tokens)

    def send_image(
        self,
        system_prompt: str,
        image_bytes: bytes,
        media_type: str,
        user_text: str,
        max_tokens: int = 1024,
    ) -> str:
        """發送圖片＋文字訊息至 Gemini（供 ocr_service 使用）。

        Args:
            system_prompt: 系統層級 prompt。
            image_bytes: 圖片二進位內容。
            media_type: 圖片 MIME type（例如 "image/jpeg"）。
            user_text: 附加的使用者文字內容。
            max_tokens: 最大回傳 token 數。

        Returns:
            Gemini 回傳的文字內容。
        """
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=media_type)
        return self._send(system_prompt, [image_part, user_text], max_tokens)

    def _send(self, system_prompt: str, contents: list, max_tokens: int) -> str:
        """呼叫 Gemini API 並回傳文字內容。

        Raises:
            RuntimeError: Gemini API 呼叫失敗（例如認證錯誤、速率限制、伺服器錯誤等）。
        """
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
        except genai_errors.APIError as exc:
            raise RuntimeError(f"Gemini API 呼叫失敗：{exc}") from exc

        return response.text or ""
