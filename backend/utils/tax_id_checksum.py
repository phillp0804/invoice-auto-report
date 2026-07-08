"""台灣統一編號檢查碼驗證演算法。

純函式，無外部依賴，方便撰寫單元測試。
"""


def validate_tax_id(tax_id: str) -> bool:
    """驗證台灣統一編號是否合法。

    使用統一編號檢查碼演算法驗證，八位數字各乘以固定權重後，
    取各乘積十位數與個位數之和，最終結果需能被 5 整除（特殊情況為第 7 碼為 7 時另有規則）。

    Args:
        tax_id: 統一編號字串（應為 8 位數字）。

    Returns:
        True 表示合法，False 表示不合法。
    """
    # TODO: 實作統編檢查碼演算法
    raise NotImplementedError
