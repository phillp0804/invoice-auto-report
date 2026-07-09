"""發票支出分類用 Prompt 模板。"""


def build_classify_invoice_system_prompt(categories: list[str]) -> str:
    """組合支出分類的系統 prompt。

    以參數傳入類別清單，而非直接匯入 classifier_service，
    避免 prompt 模組與 service 模組互相匯入造成循環依賴。

    Args:
        categories: 允許選擇的支出類別清單。

    Returns:
        系統 prompt 字串。
    """
    category_list = chr(10).join(f"- {cat}" for cat in categories)
    return f"""
你是一個專門分類企業支出的 AI 助理。
請根據發票品項內容，判斷最適合的支出類別。

可選類別（僅能從以下選項中擇一）：
{category_list}

請僅輸出 JSON 格式：
{{
  "category": "選擇的類別"
}}

注意事項：
- 僅能從上述固定類別中選擇
- 如果無法確定，請選擇「其他」
- 僅輸出 JSON，不要附加任何說明文字
""".strip()
