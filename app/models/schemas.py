from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
import uuid


class UserPreferences(BaseModel):
    """用户偏好设置"""
    style: Optional[str] = None
    colors: Optional[List[str]] = None
    occasions: Optional[List[str]] = None
    budget: Optional[str] = None
    avoid_items: Optional[List[str]] = None
    favorite_brands: Optional[List[str]] = None


class ImageMetadata(BaseModel):
    """图像元数据"""
    format: str
    mode: str
    width: int
    height: int
    resized: Optional[bool] = False
    new_width: Optional[int] = None
    new_height: Optional[int] = None


class ImageUploadResponse(BaseModel):
    """图像上传响应"""
    filename: str
    filepath: str
    content_type: str
    size: int
    metadata: ImageMetadata


class AnalysisScores(BaseModel):
    """穿搭分析评分"""
    color_harmony: float = Field(..., ge=0, le=10, description="颜色搭配协调性评分")
    style_consistency: float = Field(..., ge=0, le=10, description="风格协调性评分")
    occasion_suitability: float = Field(..., ge=0, le=10, description="场合适宜性评分")
    fashion_level: float = Field(..., ge=0, le=10, description="时尚度评分")
    personal_style: float = Field(..., ge=0, le=10, description="个人特色评分")
    budget_value: Optional[float] = Field(None, ge=0, le=10, description="预算合理性评分")
    
    @property
    def average_score(self) -> float:
        """计算平均评分"""
        scores = [self.color_harmony, self.style_consistency, self.occasion_suitability, 
                 self.fashion_level, self.personal_style]
        if self.budget_value is not None:
            scores.append(self.budget_value)
        return sum(scores) / len(scores)


class TokenUsage(BaseModel):
    """API令牌使用情况"""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class AnalysisRequest(BaseModel):
    """穿搭分析请求"""
    image_path: Optional[str] = None
    user_preferences: Optional[UserPreferences] = None
    budget_focus: bool = False


class AnalysisResponse(BaseModel):
    """穿搭分析响应"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_content: str
    scores: AnalysisScores
    suggestions: List[str]
    recommendations: List[str]
    usage: Optional[TokenUsage] = None
    request_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None