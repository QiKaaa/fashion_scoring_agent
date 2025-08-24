import os
import asyncio
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.api import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.database import close_db_connections

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

# 配置CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 挂载静态文件目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="data"), name="static")

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "欢迎使用智能穿搭分析Agent API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("应用启动中...")
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        # 在生产环境中，可能需要优雅地处理启动失败
        # 这里简单地记录错误并继续运行


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("应用关闭中...")
    try:
        # 关闭数据库连接
        await close_db_connections()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
