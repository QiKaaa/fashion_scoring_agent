"""
统一处理接口 - 自动识别意图并调用相应服务
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, Union
import time

from app.models.schemas import (
    UnifiedRequest, UnifiedResponse, IntentRequest, 
    OutfitAnalysisRequest, RecommendationRequest,
    OutfitAnalysisResponse, OutfitRecommendation
)
from app.services.intent_service import intent_service
from app.services.analysis_service import analysis_service
from app.services.recommendation_service import recommendation_service

router = APIRouter()


@router.post("/process", response_model=UnifiedResponse)
async def process_unified_request(
    request: UnifiedRequest = Body(..., description="统一处理请求")
):
    """
    统一处理接口
    
    自动识别用户意图，并调用相应的服务（多维度穿搭打分或穿搭推荐）
    """
    start_time = time.time()
    
    try:
        # 1. 意图识别
        intent_request = IntentRequest(
            message=request.message,
            image_path=request.image_path,
            user_id=request.user_id
        )
        
        intent_response = await intent_service.detect_intent(intent_request)
        
        # 2. 根据意图调用相应服务
        if intent_response.intent_type == "outfit_scoring":
            # 调用多维度穿搭打分服务
            analysis_request = OutfitAnalysisRequest(
                image_path=request.image_path,
                image_url=request.image_url,
                user_id=request.user_id,
                preferences=request.preferences
            )
            
            result = await analysis_service.analyze_outfit(
                image_path=analysis_request.image_path,
                image_url=analysis_request.image_url,
                user_preferences=request.preferences.dict() if request.preferences else None
            )
            
        else:  # outfit_recommendation
            # 调用穿搭推荐服务
            recommendation_request = RecommendationRequest(
                user_id=request.user_id,
                reference_image_path=request.image_path,
                preferences=request.preferences
            )
            
            result = await recommendation_service.get_recommendation(
                user_id=request.user_id,
                reference_image_path=request.image_path,
                preferences=request.preferences.dict() if request.preferences else None
            )
        
        # 3. 构建统一响应
        processing_time = time.time() - start_time
        response = UnifiedResponse(
            intent_type=intent_response.intent_type,
            confidence=intent_response.confidence,
            result=result,
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


@router.post("/mock-process", response_model=UnifiedResponse)
async def mock_process_unified_request(
    request: UnifiedRequest = Body(..., description="统一处理请求")
):
    """
    模拟统一处理接口（用于开发测试）
    
    使用模拟数据，无需调用大模型API
    """
    start_time = time.time()
    
    try:
        # 1. 模拟意图识别
        intent_request = IntentRequest(
            message=request.message,
            image_path=request.image_path,
            user_id=request.user_id
        )
        
        intent_response = intent_service._mock_intent_detection(intent_request)
        
        # 2. 根据意图调用相应的模拟服务
        if intent_response.intent_type == "outfit_scoring":
            # 模拟多维度穿搭打分结果
            result = analysis_service._mock_analysis_result(
                user_id=request.user_id
            )
            
        else:  # outfit_recommendation
            # 模拟穿搭推荐结果
            result = recommendation_service._mock_recommendation_result(
                user_id=request.user_id
            )
        
        # 3. 构建统一响应
        processing_time = time.time() - start_time
        response = UnifiedResponse(
            intent_type=intent_response.intent_type,
            confidence=intent_response.confidence,
            result=result,
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模拟处理请求失败: {str(e)}")