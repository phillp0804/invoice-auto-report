"""部門 ORM 模型。"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Department(Base):
    """部門資料表，對應 departments。"""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, comment="部門名稱")
    cost_center = Column(String, nullable=True, comment="成本中心代號（供報表分組使用）")

    # 關聯
    users = relationship("User", back_populates="department")
