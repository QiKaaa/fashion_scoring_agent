from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
import uuid


class IntentRequest(BaseModel):
    """意图识别请求"""
    message: str
    image_path: Optional[str] = None
    user_id: Optional[str] = None


class IntentResponse(BaseModel):
    """意图识别响应"""
    intent_type: Literal["outfit_scoring", "outfit_recommendation"]
    confidence: float = Field(..., ge=0, le=1)
    reasoning: Optional[str] = None
    raw_content: Optional[str] = None


class UserPreferences(BaseModel):
    """用户偏好设置"""
    user_id: str
    preferred_styles: List[str] = Field(default_factory=list)
    preferred_colors: List[str] = Field(default_factory=list)
    preferred_brands: List[str] = Field(default_factory=list)
    budget_range: Optional[Dict[str, float]] = None
    occasion_preferences: Optional[Dict[str, List[str]]] = None
    disliked_styles: List[str] = Field(default_factory=list)
    disliked_colors: List[str] = Field(default_factory=list)
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    age_range: Optional[str] = None
    gender: Optional[str] = None
    season_preferences: Optional[Dict[str, float]] = None
    updated_at: datetime = Field(default_factory=datetime.now)


class OutfitAnalysisRequest(BaseModel):
    """穿搭分析请求"""
    image_path: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    user_id: Optional[str] = None
    budget_focus: bool = False
    preferences: Optional[UserPreferences] = None

    @validator("image_path", "image_url")
    def validate_image_source(cls, v, values):
        if not v and not values.get("image_url") and not values.get("image_path"):
            raise ValueError("必须提供image_path或image_url")
        return v


class ScoreDimension(BaseModel):
    """评分维度"""
    score: float = Field(..., ge=1, le=10)
    reasoning: str
    improvement_suggestions: Optional[List[str]] = None


class OutfitAnalysisResponse(BaseModel):
    """穿搭分析响应"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    outfit_description: str
    color_palette: List[str]
    style_type: str
    scores: Dict[str, ScoreDimension]
    overall_score: float
    improvement_suggestions: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None


class RecommendationRequest(BaseModel):
    """穿搭推荐请求"""
    user_id: Optional[str] = None
    occasion: Optional[str] = None
    style_preference: Optional[str] = None
    color_preference: Optional[List[str]] = None
    budget_range: Optional[Dict[str, float]] = None
    season: Optional[str] = None
    reference_image_path: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class OutfitItem(BaseModel):
    """穿搭单品"""
    item_type: str
    description: str
    color: str
    style: str
    estimated_price_range: Optional[Dict[str, float]] = None
    brand_suggestions: Optional[List[str]] = None
    image_url: Optional[HttpUrl] = None


class OutfitRecommendation(BaseModel):
    """穿搭推荐"""
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    outfit_items: List[OutfitItem]
    style_description: str
    occasion_suitability: List[str]
    estimated_total_budget: Optional[Dict[str, float]] = None
    styling_tips: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None


class UnifiedRequest(BaseModel):
    """统一处理请求"""
    message: str
    image_path: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    user_id: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class UnifiedResponse(BaseModel):
    """统一处理响应"""
    intent_type: Literal["outfit_scoring", "outfit_recommendation"]
    confidence: float
    result: Union[OutfitAnalysisResponse, OutfitRecommendation]
    processing_time: float