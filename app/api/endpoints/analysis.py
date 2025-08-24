from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Query, status
from pydantic import parse_obj_as
import json

from app.models.schemas import (
    OutfitAnalysisRequest as AnalysisRequest, 
    OutfitAnalysisResponse as AnalysisResponse, 
    UserPreferences
)

# 定义错误响应模型，因为schemas.py中没有
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    detail: str

class ImageUploadResponse(BaseModel):
    filepath: str
    filename: str
from app.services.analysis_service import analysis_service
from app.services.image_service import image_service


router = APIRouter()


@router.post("/analyze/upload", response_model=AnalysisResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    user_preferences: Optional[str] = Form(None),
    budget_focus: bool = Form(False)
):
    """
    上传并分析穿搭照片
    
    - **file**: 要上传的穿搭照片
    - **user_preferences**: 用户偏好设置（JSON字符串）
    - **budget_focus**: 是否关注预算维度
    """
    try:
        # 解析用户偏好
        preferences = None
        if user_preferences:
            try:
                preferences = parse_obj_as(UserPreferences, json.loads(user_preferences))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的用户偏好格式: {str(e)}"
                )
        
        # 保存上传的图像
        upload_result = await image_service.save_upload(file)
        
        # 分析穿搭
        analysis_result = await analysis_service.analyze_outfit(
            image_path=upload_result["filepath"],
            user_preferences=preferences.dict() if preferences else None,
            budget_focus=budget_focus
        )
        
        if "error" in analysis_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=analysis_result["error"]
            )
        
        return AnalysisResponse(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析穿搭时出错: {str(e)}"
        )


@router.post("/analyze/path", response_model=AnalysisResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def analyze_image_by_path(
    request: AnalysisRequest
):
    """
    通过路径分析穿搭照片
    
    - **image_path**: 图像文件路径
    - **user_preferences**: 用户偏好设置
    - **budget_focus**: 是否关注预算维度
    """
    try:
        if not request.image_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供image_path参数"
            )
        
        # 分析穿搭
        analysis_result = await analysis_service.analyze_outfit(
            image_path=request.image_path,
            user_preferences=request.user_preferences.dict() if request.user_preferences else None,
            budget_focus=request.budget_focus
        )
        
        if "error" in analysis_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=analysis_result["error"]
            )
        
        return AnalysisResponse(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析穿搭时出错: {str(e)}"
        )