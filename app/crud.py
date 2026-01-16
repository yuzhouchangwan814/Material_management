from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import Material
from app.schemas import MaterialCreate

# 1. 创建材料
async def create_material(db: AsyncSession, material: MaterialCreate):
    """
    添加新材料：将 Pydantic 模型转换为 SQLAlchemy 模型并保存
    """
    # 将 schema 数据转换为数据库模型实例
    db_material = Material(
        cas_number=material.cas_number,
        properties=material.properties
    )
    db.add(db_material)
    # 提交到数据库 (由于 get_database 依赖里也有 commit，
    # 这里显式 commit 可以确保数据立刻写入并获取生成的 ID)
    await db.commit()
    await db.refresh(db_material) # 刷新以获取数据库生成的 id 和时间戳
    return db_material

# 2. 根据 CAS 号查询单个材料
async def get_material_by_cas(db: AsyncSession, cas_number: str):
    """
    查询单个：使用 select 语句配合 where 条件
    """
    result = await db.execute(
        select(Material).where(Material.cas_number == cas_number)
    )
    # scalars().first() 返回第一个对象，如果没有则返回 None
    return result.scalars().first()

# 3. 查询所有材料列表
async def get_all_materials(db: AsyncSession):
    """
    查询所有：返回材料列表
    """
    result = await db.execute(select(Material))
    return result.scalars().all()

# 4. 根据 CAS 号删除材料
async def delete_material_by_cas(db: AsyncSession, cas_number: str):
    """
    删除记录：先查询是否存在，存在则删除
    """
    # 也可以直接使用 delete 语句以提高效率
    db_material = await get_material_by_cas(db, cas_number)
    if db_material:
        await db.delete(db_material)
        await db.commit()
        return True
    return False
