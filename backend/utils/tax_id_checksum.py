"""台灣統一編號檢查碼驗證演算法。

純函式，無外部依賴，方便撰寫單元測試。
"""

# 統一編號每一碼對應的權重
_WEIGHTS = [1, 2, 1, 2, 1, 2, 4, 1]


def _sum_digits(n: int) -> int:
    """將數字的十位數與個位數相加。

    例如：18 → 1 + 8 = 9，5 → 0 + 5 = 5。
    """
    return (n // 10) + (n % 10)


def validate_tax_id(tax_id: str) -> bool:
    """驗證台灣統一編號是否合法。

    演算法規則：
    1. 統編必須是 8 碼純數字
    2. 每一碼分別乘上權重 [1, 2, 1, 2, 1, 2, 4, 1]
    3. 乘積若為兩位數，需把十位數跟個位數相加
    4. 全部加總後，若為 10 的倍數則合法
    5. 例外：第 7 碼為 "7" 時，加總結果 +1 後為 10 的倍數亦視為合法

    Args:
        tax_id: 統一編號字串（應為 8 位數字）。

    Returns:
        True 表示合法，False 表示不合法。
    """
    # 格式檢查：必須恰好 8 碼純數字
    if not isinstance(tax_id, str) or len(tax_id) != 8 or not tax_id.isdigit():
        return False

    # 計算各碼乘以權重後的十位數 + 個位數之加總
    total = sum(
        _sum_digits(int(digit) * weight)
        for digit, weight in zip(tax_id, _WEIGHTS)
    )

    # 一般規則：加總為 10 的倍數即合法
    if total % 10 == 0:
        return True

    # 例外規則：第 7 碼為 "7" 時，加總 +1 後為 10 的倍數亦合法
    if tax_id[6] == "7" and (total + 1) % 10 == 0:
        return True

    return False


def is_company_tax_id(buyer_tax_id: str, company_tax_id: str) -> bool:
    """比對發票上的買方統編是否為本公司統編。

    用於判斷員工上傳的發票是否確實開立給本公司，
    避免個人消費發票混入報帳流程。

    Args:
        buyer_tax_id: 發票上的買方統編。
        company_tax_id: 系統設定的公司統編。

    Returns:
        True 表示買方統編與公司統編一致，False 表示不一致。
    """
    # 兩者都必須是合法統編格式才有比對意義
    if not validate_tax_id(buyer_tax_id) or not validate_tax_id(company_tax_id):
        return False

    return buyer_tax_id == company_tax_id


def classify_buyer_tax_id(buyer_tax_id: str | None, company_tax_id: str) -> str | None:
    """判斷買方統編狀態，供總務審核時標註提醒。

    財政部規範：一般消費者未提供買方統編時視為 "00000000"，
    此函式將其歸類為「未打」而非「不符」，避免誤導總務誤判為異常發票。

    Args:
        buyer_tax_id: 發票上的買方統編（可能為 None 或 "00000000"）。
        company_tax_id: 系統設定的公司統編，未設定時無法比對是否相符。

    Returns:
        "missing" 表示未打統編、"mismatch" 表示與公司統編不符、
        None 表示相符或公司統編未設定（無法判斷）。
    """
    if not buyer_tax_id or buyer_tax_id == "00000000":
        return "missing"

    if not company_tax_id:
        return None

    if not is_company_tax_id(buyer_tax_id, company_tax_id):
        return "mismatch"

    return None
