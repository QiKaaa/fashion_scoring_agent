"""
数据库初始化模块
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine, Base, init_redis_pool, get_redis_client
from app.models.memory_models import Memory, MemoryRelation, MemoryConsolidation

logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """创建数据库表"""
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建成功")
    except SQLAlchemyError as e:
        logger.error(f"创建数据库表时出错: {e}")
        raise


async def setup_extensions() -> None:
    """设置 PostgreSQL 扩展"""
    try:
        async with engine.begin() as conn:
            # 检查并创建 pgvector 扩展
            result = await conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
            if result.scalar() is None:
                # 创建 pgvector 扩展
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("pgvector 扩展创建成功")
            else:
                logger.info("pgvector 扩展已存在")
                
            # 检查并创建 pg_trgm 扩展（用于文本搜索的 GIN 索引）
            result = await conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'"))
            if result.scalar() is None:
                # 创建 pg_trgm 扩展
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                logger.info("pg_trgm 扩展创建成功")
            else:
                logger.info("pg_trgm 扩展已存在")
    except SQLAlchemyError as e:
        logger.error(f"设置 PostgreSQL 扩展时出错: {e}")
        logger.warning("请确保您的 PostgreSQL 已安装必要的扩展")


async def init_redis() -> None:
    """初始化 Redis"""
    try:
        await init_redis_pool()
        redis_client = await get_redis_client()
        await redis_client.ping()
        logger.info("Redis 连接成功")
    except Exception as e:
        logger.error(f"初始化 Redis 时出错: {e}")
        raise


async def init_db() -> None:
    """初始化数据库"""
    try:
        # 设置 PostgreSQL 扩展（在创建表之前）
        await setup_extensions()
        
        # 创建数据库表
        await create_tables()
        
        # 初始化 Redis
        await init_redis()
        
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")
        raise
