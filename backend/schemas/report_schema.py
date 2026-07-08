"""報表相關的 Pydantic schema。"""

from decimal import Decimal

from pydantic import BaseModel


class CategorySummary(BaseModel):
    """依類別彙整的摘要。"""
    category: str
    total_amount: Decimal
    count: int


class EmployeeSummary(BaseModel):
    """依員工彙整的摘要。"""
    user_id: int
    user_name: str
    total_amount: Decimal
    count: int


class DepartmentSummary(BaseModel):
    """依部門彙整的摘要。"""
    department_id: int
    department_name: str
    total_amount: Decimal
    count: int


class DashboardResponse(BaseModel):
    """總務儀表板回傳 schema。"""
    total_amount: Decimal
    total_count: int
    pending_count: int  # 待審核件數
    by_category: list[CategorySummary]
    by_employee: list[EmployeeSummary]
    by_department: list[DepartmentSummary]


class ReportExportRequest(BaseModel):
    """報表匯出請求 schema。"""
    year: int
    month: int
    group_by: str = "department"  # "department" / "employee" / "category"
