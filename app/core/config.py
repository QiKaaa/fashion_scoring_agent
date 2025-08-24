"""
应用配置
"""

import os
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Any, Union
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()   

class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    """应用配置"""
    # 应用信息
    APP_NAME: str = "智能穿搭分析Agent"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "基于Qwen-VL-Chat API和AutoGen的智能穿搭分析系统"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "fashion_scoring_agent")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Qwen-VL-Chat API配置
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "your-api-key-here")
    QWEN_API_BASE: str = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/api/v1")
    QWEN_MODEL_NAME: str = os.getenv("QWEN_MODEL_NAME", "qwen-vl-chat")
    
    # 文件存储配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/images")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置"""
    return Settings()


settings = get_settings()