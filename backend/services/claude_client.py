"""Claude API 共用客戶端。

統一管理 API Key 讀取、錯誤處理、重試機制，
供 ocr_service 和 classifier_service 共用。
"""

import anthropic

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

    def send_message(
        self,
        system_prompt: str,
        user_content: list,
        max_tokens: int = 1024,
    ) -> str:
        """發送訊息至 Claude API。

        Args:
            system_prompt: 系統層級 prompt。
            user_content: 使用者內容清單（支援文字與圖片）。
            max_tokens: 最大回傳 token 數。

        Returns:
            Claude 回傳的文字內容（合併所有 text 區塊）。

        Raises:
            RuntimeError: Claude API 呼叫失敗（例如認證錯誤、額度超過重試上限的
                速率限制、伺服器錯誤等，SDK 已內建重試但仍失敗時拋出）。
        """
        try:
            response = self._client.messages.create(
                model=_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
        except anthropic.APIError as exc:
            raise RuntimeError(f"Claude API 呼叫失敗：{exc}") from exc

        return "".join(
            block.text for block in response.content if block.type == "text"
        )
