"""Claude API 共用客戶端。

統一管理 API Key 讀取、錯誤處理、重試機制，
供 ocr_service 和 classifier_service 共用。
"""


class ClaudeClient:
    """Claude API 底層呼叫客戶端。"""

    def __init__(self, api_key: str):
        """初始化 Claude API 客戶端。

        Args:
            api_key: Anthropic API 金鑰。
        """
        self.api_key = api_key
        # TODO: 初始化 anthropic.Anthropic 客戶端

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
            Claude 回傳的文字內容。
        """
        # TODO: 呼叫 Claude API，包含錯誤處理與重試機制
        raise NotImplementedError
