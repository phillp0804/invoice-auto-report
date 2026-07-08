"""AI 支出分類服務。

呼叫 Claude API，依照固定分類清單判斷發票的支出類別。
"""

# 預定義的支出分類清單
EXPENSE_CATEGORIES = [
    "餐飲",
    "交通",
    "辦公用品",
    "設備",
    "通訊",
    "住宿",
    "其他",
]


class ClassifierService:
    """AI 支出分類服務。"""

    def __init__(self, api_key: str):
        """初始化 ClassifierService。

        Args:
            api_key: Anthropic API 金鑰。
        """
        self.api_key = api_key
        self.categories = EXPENSE_CATEGORIES

    def classify(self, items: list[str], amount: float | None = None) -> str:
        """判斷支出類別。

        Args:
            items: 發票品項清單。
            amount: 金額（輔助判斷）。

        Returns:
            分類結果（限定在 EXPENSE_CATEGORIES 範圍內）。
        """
        # TODO: 組合 Prompt（從 prompts/ 讀取模板）
        # TODO: 呼叫 Claude API
        # TODO: 解析回傳結果，確保在固定分類清單內
        raise NotImplementedError
