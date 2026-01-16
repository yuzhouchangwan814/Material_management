import asyncio
from aiomysql import OperationalError
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from contextlib import asynccontextmanager

from app.database import get_database, async_engine
from app.models import Base
from app.schemas import MaterialCreate, MaterialResponse
from app import crud

# 1. 定义生命周期：在应用启动时自动创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 重试逻辑：尝试 5 次，每次间隔 2 秒
    for i in range(5):
        try:
            async with async_engine.begin() as conn:
                # 自动创建表
                await conn.run_sync(Base.metadata.create_all)
            break # 成功则跳出循环
        except (OperationalError, Exception) as e:
            if i == 4: raise e # 最后一次失败则抛出异常
            print(f"数据库尚未就绪，正在重试... ({i+1}/5)")
            await asyncio.sleep(2)
    yield  # --- 应用运行中 ---
    # 【关闭阶段】
    # 当应用停止（如 Ctrl+C 或 Docker 停止）时执行
    print("正在关闭数据库连接池...")
    await async_engine.dispose()
    print("数据库连接已释放。")

app = FastAPI(
    title="材料属性管理 API",
    description="基于 FastAPI + MySQL 的材料 CAS 号及性质管理系统",
    lifespan=lifespan
)

# 2. 路由实现
@app.post("/materials/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def add_material(material: MaterialCreate, db: AsyncSession = Depends(get_database)):
    """
    添加新材料。
    - 如果 CAS 号已存在，返回 409 Conflict。
    """
    # 检查唯一性
    existing = await crud.get_material_by_cas(db, material.cas_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"CAS号 {material.cas_number} 已存在"
        )
    return await crud.create_material(db, material)

@app.get("/materials/", response_model=List[MaterialResponse])
async def read_materials(db: AsyncSession = Depends(get_database)):
    """
    查询所有材料列表。
    """
    return await crud.get_all_materials(db)

@app.get("/materials/{cas_number}", response_model=MaterialResponse)
async def read_material(cas_number: str, db: AsyncSession = Depends(get_database)):
    """
    根据 CAS 号查询单个材料详细信息。
    - 如果未找到，返回 404 Not Found。
    """
    db_material = await crud.get_material_by_cas(db, cas_number)
    if db_material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="未找到该材料记录"
        )
    return db_material

@app.delete("/materials/{cas_number}", status_code=status.HTTP_200_OK)
async def remove_material(cas_number: str, db: AsyncSession = Depends(get_database)):
    """
    根据 CAS 号删除指定的材料记录。
    - 如果未找到，返回 404 Not Found。
    """
    success = await crud.delete_material_by_cas(db, cas_number)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="删除失败，未找到该材料记录"
        )
    return {"message": f"材料 {cas_number} 已成功删除"}
