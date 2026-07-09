"""AI 支出分類服務。

呼叫 Claude API，依照固定分類清單判斷發票的支出類別。
"""

import json

from services.claude_client import ClaudeClient
from services.prompts.classify_invoice_prompt import build_classify_invoice_system_prompt

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

# AI 回傳類別不在清單內、或解析失敗時的保底分類
_FALLBACK_CATEGORY = "其他"


class ClassifierService:
    """AI 支出分類服務。"""

    def __init__(self, api_key: str):
        """初始化 ClassifierService。

        Args:
            api_key: Anthropic API 金鑰。
        """
        self.claude_client = ClaudeClient(api_key)
        self.categories = EXPENSE_CATEGORIES

    def classify(self, items: list[str], amount: float | None = None) -> str:
        """判斷支出類別。

        Args:
            items: 發票品項清單。
            amount: 金額（輔助判斷）。

        Returns:
            分類結果（限定在 EXPENSE_CATEGORIES 範圍內；AI 回傳超出清單範圍
            或無法解析時，回傳保底分類「其他」，不讓 AI 自由生成類別名稱）。
        """
        item_text = "、".join(items) if items else "（無品項資訊）"
        user_text = f"品項：{item_text}"
        if amount is not None:
            user_text += f"\n金額：{amount}"

        response_text = self.claude_client.send_message(
            system_prompt=build_classify_invoice_system_prompt(self.categories),
            user_content=[{"type": "text", "text": user_text}],
        )

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            return _FALLBACK_CATEGORY

        category = data.get("category")
        return category if category in self.categories else _FALLBACK_CATEGORY
