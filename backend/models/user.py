"""使用者 ORM 模型。"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """使用者資料表，對應 users。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, comment="姓名")
    email = Column(String, unique=True, nullable=False, comment="Email（對應 Firebase 帳號）")
    role = Column(String, nullable=False, comment="角色：employee 或 admin（總務）")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="所屬部門 FK")

    # 關聯
    department = relationship("Department", back_populates="users")
    invoices = relationship("Invoice", back_populates="user")
