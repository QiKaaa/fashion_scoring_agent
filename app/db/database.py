"""
数据库连接模块
"""

import asyncio
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import redis.asyncio as aioredis

from app.core.config import settings

# PostgreSQL 连接
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL and DATABASE_URL.startswith('postgresql:'):
    DATABASE_URL = DATABASE_URL.replace('postgresql:', 'postgresql+asyncpg:', 1)

# 创建异步引擎
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建异步会话
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 创建 Base 类
Base = declarative_base()

# Redis 连接
redis_url = f"redis://"
if settings.REDIS_PASSWORD:
    redis_url += f":{settings.REDIS_PASSWORD}@"
redis_url += f"{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

# Redis 连接池
redis_pool = None


async def init_redis_pool() -> None:
    """初始化 Redis 连接池"""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.ConnectionPool.from_url(
            redis_url,
            max_connections=10,
            decode_responses=True
        )


async def get_redis_client() -> aioredis.Redis:
    """获取 Redis 客户端"""
    if redis_pool is None:
        await init_redis_pool()
    return aioredis.Redis(connection_pool=redis_pool)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connections() -> None:
    """关闭数据库连接"""
    await engine.dispose()
    if redis_pool:
        await redis_pool.disconnect()


async def check_db_connection() -> Dict[str, Any]:
    """检查数据库连接状态"""
    status = {
        "postgresql": False,
        "redis": False,
        "details": {}
    }
    
    # 检查 PostgreSQL 连接
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        status["postgresql"] = True
        status["details"]["postgresql"] = "连接成功"
    except Exception as e:
        status["details"]["postgresql"] = f"连接失败: {str(e)}"
    
    # 检查 Redis 连接
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        status["redis"] = True
        status["details"]["redis"] = "连接成功"
    except Exception as e:
        status["details"]["redis"] = f"连接失败: {str(e)}"
    
    return status