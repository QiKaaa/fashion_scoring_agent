import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.api import api_router
from app.core.config import settings


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="智能穿搭分析Agent API",
    version="0.1.0",
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


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)