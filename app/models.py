from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, JSON, func
from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict

# 1. 定义基类：统一管理时间戳字段
class Base(DeclarativeBase):
    # 根据图片要求，字段名改为 created_at
    create_time: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),  # 由数据库生成默认时间
        comment="创建时间"
    )
    # 根据图片要求，字段名改为 updated_at
    update_time: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(),        # 自动更新时间
        comment="更新时间"
    )

# 2. 定义材料模型类
class Material(Base):
    __tablename__ = "materials"

    # id: INT, PRIMARY KEY, AUTO_INCREMENT
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="自增主键")
    
    # cas_number: VARCHAR(50), UNIQUE, NOT NULL
    cas_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="CAS号，唯一标识")
    
    # properties: JSON, NOT NULL (SQLAlchemy 的 JSON 类型会自动处理字典转换)
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="材料性质，存储JSON对象")

# 3. 定义 Pydantic 模型 (用于 FastAPI 请求和响应的校验)
class MaterialBase(BaseModel):
    cas_number: str
    properties: Dict[str, Any]  # 接收 JSON 格式，例如 {"密度": "2.7 g/cm³"}

class MaterialCreate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: int
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True # 允许从 SQLAlchemy 模型对象转换
        