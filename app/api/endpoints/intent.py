"""
意图识别API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional
import time

from app.models.schemas import IntentRequest, IntentResponse
from app.services.intent_service import intent_service

router = APIRouter()


@router.post("/detect", response_model=IntentResponse)
async def detect_intent(
    request: IntentRequest = Body(..., description="意图识别请求")
):
    """
    检测用户意图
    
    根据用户输入的文本和/或图像，判断用户意图是多维度穿搭打分还是穿搭推荐
    """
    try:
        # 调用意图识别服务
        response = await intent_service.detect_intent(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"意图识别失败: {str(e)}")


@router.post("/mock-detect", response_model=IntentResponse)
async def mock_detect_intent(
    request: IntentRequest = Body(..., description="意图识别请求")
):
    """
    模拟检测用户意图（用于开发测试）
    
    使用简单的关键词匹配算法，无需调用大模型API
    """
    try:
        # 调用模拟意图识别
        response = intent_service._mock_intent_detection(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模拟意图识别失败: {str(e)}")