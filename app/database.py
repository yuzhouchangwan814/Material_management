import os
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from urllib.parse import quote

# 1. 从环境变量读取配置 
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "default_password")
DB_HOST = os.getenv("DB_HOST", "db")  # 在 Docker Compose 中，这里通常是服务名 "db"
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "material_db")

# 对密码进行转义处理，防止特殊字符干扰 URL 解析
safe_password = quote("" + DB_PASSWORD + "")

# 构造异步连接字符串 (使用 aiomysql)
# 注意：生产环境务必指定 charset=utf8mb4 以支持 JSON 字段中的特殊符号
# ASYNC_DATABASE_URL = f"mysql+aiomysql://root:{safe_password}@localhost:3306/material_db?charset=utf8mb4"
ASYNC_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


# 2. 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,      # 输出 SQL 日志，面试演示时很有用   
    pool_size=10,     # 连接池活跃数量  
    max_overflow=20,    # 额外允许的连接数
    # 增加自动重试和回收，应对容器启动初期的不稳定性
    pool_pre_ping=True,      # 每次取连接前先“ping”一下数据库
    pool_recycle=3600,      # 每小时回收连接
# 新增以下参数：给连接过程增加 10 秒的超时等待，防止 MySQL 重启瞬间连接失败
    connect_args={
        "connect_timeout": 10}
)

# 3. 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False  # 核心配置：防止提交后对象属性失效
)

# 4. 依赖项：用于在 FastAPI 路由中获取数据库会话
async def get_database():
    """
    异步数据库会话生成器
    使用方式：db: AsyncSession = Depends(get_database)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 返回会话给路由处理函数
            await session.commit()  # 执行成功，统一提交
        except Exception:
            await session.rollback()  # 发生异常，回滚事务
            raise  # 将错误继续抛出，让 FastAPI 返回 500
        finally:
            await session.close()  # 归还连接到连接池