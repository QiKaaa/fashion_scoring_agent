"""
记忆系统API端点 - 提供记忆管理接口
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from app.models.schemas import ErrorResponse
from app.services.memory_service import memory_service


router = APIRouter()


class SessionMemoryRequest(BaseModel):
    """会话记忆请求"""
    session_id: Optional[str] = Field(None, description="会话ID，如不提供则自动生成")
    memory_data: Dict[str, Any] = Field(..., description="会话记忆数据")
    ttl: Optional[int] = Field(3600, description="过期时间（秒）")


class SessionMemoryResponse(BaseModel):
    """会话记忆响应"""
    session_id: str
    success: bool
    message: str


class ConversationEntryRequest(BaseModel):
    """对话记录请求"""
    role: str = Field(..., description="角色（user/assistant）")
    content: str = Field(..., description="对话内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class MemoryRequest(BaseModel):
    """长期记忆请求"""
    user_id: str = Field(..., description="用户ID")
    memory_type: str = Field(..., description="记忆类型")
    content: Dict[str, Any] = Field(..., description="记忆内容")
    importance_score: Optional[float] = Field(None, description="重要性分数")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class MemoryResponse(BaseModel):
    """长期记忆响应"""
    memory_id: int
    success: bool
    message: str


class MemoryQueryRequest(BaseModel):
    """记忆查询请求"""
    user_id: str = Field(..., description="用户ID")
    query_context: str = Field(..., description="查询上下文")
    memory_types: Optional[List[str]] = Field(None, description="记忆类型列表")
    limit: Optional[int] = Field(5, description="返回记忆数量限制")
    time_window_days: Optional[int] = Field(90, description="时间窗口（天）")


@router.post("/session", response_model=SessionMemoryResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def save_session_memory(
    request: SessionMemoryRequest = Body(..., description="会话记忆请求")
):
    """
    保存会话记忆
    
    - **session_id**: 会话ID，如不提供则自动生成
    - **memory_data**: 会话记忆数据
    - **ttl**: 过期时间（秒）
    """
    try:
        # 生成会话ID（如果未提供）
        session_id = request.session_id or f"sess_{uuid.uuid4()}"
        
        # 保存会话记忆
        success = await memory_service.save_session_memory(
            session_id=session_id,
            memory_data=request.memory_data,
            ttl=request.ttl
        )
        
        if success:
            return SessionMemoryResponse(
                session_id=session_id,
                success=True,
                message="会话记忆保存成功"
            )
        else:
            raise HTTPException(status_code=500, detail="会话记忆保存失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存会话记忆时出错: {str(e)}")


@router.get("/session/{session_id}", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_session_memory(
    session_id: str = Path(..., description="会话ID")
):
    """
    获取会话记忆
    
    - **session_id**: 会话ID
    """
    try:
        # 获取会话记忆
        memory_data = await memory_service.get_session_memory(session_id)
        
        if memory_data:
            return memory_data
        else:
            raise HTTPException(status_code=404, detail=f"未找到会话记忆: {session_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话记忆时出错: {str(e)}")


@router.post("/session/{session_id}/conversation", response_model=SessionMemoryResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def add_conversation_entry(
    session_id: str = Path(..., description="会话ID"),
    request: ConversationEntryRequest = Body(..., description="对话记录请求")
):
    """
    添加对话记录到会话记忆
    
    - **session_id**: 会话ID
    - **role**: 角色（user/assistant）
    - **content**: 对话内容
    - **metadata**: 元数据
    """
    try:
        # 添加对话记录
        success = await memory_service.add_conversation_entry(
            session_id=session_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata
        )
        
        if success:
            return SessionMemoryResponse(
                session_id=session_id,
                success=True,
                message="对话记录添加成功"
            )
        else:
            raise HTTPException(status_code=500, detail="对话记录添加失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加对话记录时出错: {str(e)}")


@router.post("/long-term", response_model=MemoryResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def store_long_term_memory(
    request: MemoryRequest = Body(..., description="长期记忆请求")
):
    """
    存储长期记忆
    
    - **user_id**: 用户ID
    - **memory_type**: 记忆类型
    - **content**: 记忆内容
    - **importance_score**: 重要性分数（可选）
    - **tags**: 标签（可选）
    - **metadata**: 元数据（可选）
    """
    try:
        # 存储长期记忆
        memory_id = await memory_service.store_memory(
            user_id=request.user_id,
            memory_type=request.memory_type,
            content=request.content,
            importance_score=request.importance_score,
            tags=request.tags,
            metadata=request.metadata
        )
        
        if memory_id:
            return MemoryResponse(
                memory_id=memory_id,
                success=True,
                message="长期记忆存储成功"
            )
        else:
            raise HTTPException(status_code=500, detail="长期记忆存储失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"存储长期记忆时出错: {str(e)}")


@router.get("/long-term/{memory_id}", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_long_term_memory(
    memory_id: int = Path(..., description="记忆ID")
):
    """
    获取长期记忆
    
    - **memory_id**: 记忆ID
    """
    try:
        # 获取长期记忆
        memory = await memory_service.retrieve_memory(memory_id)
        
        if memory:
            return memory
        else:
            raise HTTPException(status_code=404, detail=f"未找到记忆: {memory_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取长期记忆时出错: {str(e)}")


@router.get("/long-term/user/{user_id}/type/{memory_type}", responses={500: {"model": ErrorResponse}})
async def get_memories_by_type(
    user_id: str = Path(..., description="用户ID"),
    memory_type: str = Path(..., description="记忆类型"),
    limit: int = Query(10, description="返回记忆数量限制"),
    offset: int = Query(0, description="分页偏移量")
):
    """
    按类型获取长期记忆
    
    - **user_id**: 用户ID
    - **memory_type**: 记忆类型
    - **limit**: 返回记忆数量限制
    - **offset**: 分页偏移量
    """
    try:
        # 按类型获取长期记忆
        memories = await memory_service.retrieve_memories_by_type(
            user_id=user_id,
            memory_type=memory_type,
            limit=limit,
            offset=offset
        )
        
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"按类型获取长期记忆时出错: {str(e)}")


@router.post("/long-term/query", responses={500: {"model": ErrorResponse}})
async def query_relevant_memories(
    request: MemoryQueryRequest = Body(..., description="记忆查询请求")
):
    """
    查询相关记忆
    
    - **user_id**: 用户ID
    - **query_context**: 查询上下文
    - **memory_types**: 记忆类型列表（可选）
    - **limit**: 返回记忆数量限制（可选）
    - **time_window_days**: 时间窗口（天）（可选）
    """
    try:
        # 查询相关记忆
        memories = await memory_service.retrieve_relevant_memories(
            user_id=request.user_id,
            query_context=request.query_context,
            memory_types=request.memory_types,
            limit=request.limit,
            time_window_days=request.time_window_days
        )
        
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询相关记忆时出错: {str(e)}")


@router.post("/long-term/{memory_id}/forget", response_model=MemoryResponse, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def forget_memory(
    memory_id: int = Path(..., description="记忆ID"),
    reason: str = Query("manual", description="遗忘原因")
):
    """
    遗忘记忆
    
    - **memory_id**: 记忆ID
    - **reason**: 遗忘原因
    """
    try:
        # 遗忘记忆
        success = await memory_service.forget_memory(memory_id, reason)
        
        if success:
            return MemoryResponse(
                memory_id=memory_id,
                success=True,
                message=f"记忆遗忘成功，原因: {reason}"
            )
        else:
            raise HTTPException(status_code=500, detail="记忆遗忘失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"遗忘记忆时出错: {str(e)}")


@router.post("/maintenance/consolidate/{user_id}", response_model=Dict[str, Any], responses={500: {"model": ErrorResponse}})
async def run_memory_consolidation(
    user_id: str = Path(..., description="用户ID"),
    threshold: int = Query(3, description="整合阈值")
):
    """
    运行记忆整合
    
    - **user_id**: 用户ID
    - **threshold**: 整合阈值
    """
    try:
        # 运行记忆整合
        success = await memory_service.consolidate_memories(user_id, threshold)
        
        return {
            "success": success,
            "message": "记忆整合处理完成",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"运行记忆整合时出错: {str(e)}")


@router.post("/maintenance/forget/{user_id}", response_model=Dict[str, Any], responses={500: {"model": ErrorResponse}})
async def run_intelligent_forgetting(
    user_id: str = Path(..., description="用户ID")
):
    """
    运行智能遗忘
    
    - **user_id**: 用户ID
    """
    try:
        # 运行智能遗忘
        success = await memory_service.intelligent_forgetting(user_id)
        
        return {
            "success": success,
            "message": "智能遗忘处理完成",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"运行智能遗忘时出错: {str(e)}")