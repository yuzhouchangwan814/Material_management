from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from datetime import datetime

# 基础模型，包含共有的字段
class MaterialBase(BaseModel):
    # 使用 Field 添加校验和描述
    cas_number: str = Field(
        ..., 
        pattern=r"^\d{2,7}-\d{2}-\d$", # 简单的 CAS 号正则校验
        description="材料的 CAS 登记号",
        examples=["7429-90-5"]
    )
    properties: Dict[str, Any] = Field(
        ..., 
        description="材料的物理/化学性质",
        examples=[{"密度": "2.7 g/cm³", "熔点": "660 °C"}]
    )

# 用于创建操作的 Schema (POST)
class MaterialCreate(MaterialBase):
    pass

# 用于更新操作的 Schema (PATCH/PUT)
# 字段设为 Optional，允许只更新 properties 而不改动其他
class MaterialUpdate(BaseModel):
    properties: Optional[Dict[str, Any]] = None

# 用于响应的 Schema (GET/POST 返回结果)
class MaterialResponse(MaterialBase):
    id: int
    create_time: datetime
    update_time: datetime

    # Pydantic v2 的写法：允许从 SQLAlchemy 模型读取数据
    model_config = ConfigDict(from_attributes=True)

# 用于列表查询的分页响应 (可选，显得更专业)
class MaterialListResponse(BaseModel):
    total: int
    items: list[MaterialResponse]