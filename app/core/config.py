import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, BaseSettings, validator


class Settings(BaseSettings):
    """应用配置设置"""
    
    # 基础配置
    PROJECT_NAME: str = "智能穿搭分析Agent"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Qwen-VL-Chat API配置
    QWEN_API_KEY: Optional[str] = os.getenv("QWEN_API_KEY")
    QWEN_API_BASE: str = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/api/v1")
    QWEN_MODEL_VERSION: str = os.getenv("QWEN_MODEL_VERSION", "qwen-vl-plus")
    QWEN_API_TIMEOUT: int = 60
    QWEN_MAX_TOKENS: int = 1500
    QWEN_TEMPERATURE: float = 0.7
    
    # 图像处理配置
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    IMAGE_RESIZE_WIDTH: int = 1024
    
    # 数据库配置 (占位，稍后配置)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Redis配置 (占位，稍后配置)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 文件存储配置
    UPLOAD_DIR: str = "data/images"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()