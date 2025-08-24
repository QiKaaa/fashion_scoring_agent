"""
Agent记忆系统服务 - 实现长期记忆管理
"""

import os
import json
import math
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import numpy as np
from loguru import logger
import aioredis
import asyncpg
from pydantic import BaseModel

from app.core.config import settings
from app.models.schemas import UserPreferences


class MemoryService:
    """Agent记忆系统服务"""
    
    def __init__(self):
        """初始化Agent记忆系统服务"""
        self.redis = None
        self.pg_pool = None
        self.initialized = False
    
    async def initialize(self):
        """初始化连接"""
        if self.initialized:
            return
            
        # 初始化Redis连接
        try:
            self.redis = await aioredis.create_redis_pool(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                minsize=1,
                maxsize=10
            )
            logger.info("Redis连接初始化成功")
        except Exception as e:
            logger.error(f"Redis连接初始化失败: {str(e)}")
            self.redis = None
        
        # 初始化PostgreSQL连接
        try:
            self.pg_pool = await asyncpg.create_pool(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT
            )
            logger.info("PostgreSQL连接初始化成功")
            
            # 确保记忆表存在
            await self._ensure_memory_tables()
        except Exception as e:
            logger.error(f"PostgreSQL连接初始化失败: {str(e)}")
            self.pg_pool = None
        
        self.initialized = True
    
    async def _ensure_memory_tables(self):
        """确保记忆相关的数据表存在"""
        async with self.pg_pool.acquire() as conn:
            # 检查pgvector扩展
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                logger.info("pgvector扩展已启用")
            except Exception as e:
                logger.error(f"pgvector扩展启用失败: {str(e)}")
            
            # 创建记忆表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_memories (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    memory_type VARCHAR(50) NOT NULL,
                    content JSONB NOT NULL,
                    embedding vector(512),
                    importance_score FLOAT DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    tags TEXT[],
                    meta_info JSONB,
                    forgotten BOOLEAN DEFAULT FALSE,
                    forgotten_at TIMESTAMP,
                    forgotten_reason VARCHAR(50)
                );
            """)
            
            # 创建记忆关联表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_associations (
                    id SERIAL PRIMARY KEY,
                    source_memory_id INTEGER REFERENCES agent_memories(id),
                    target_memory_id INTEGER REFERENCES agent_memories(id),
                    association_type VARCHAR(50),
                    strength FLOAT DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 创建记忆访问日志表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_access_log (
                    id SERIAL PRIMARY KEY,
                    memory_id INTEGER REFERENCES agent_memories(id),
                    access_type VARCHAR(20),
                    context JSONB,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 创建索引
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_user_type ON agent_memories(user_id, memory_type);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON agent_memories(importance_score DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_created_at ON agent_memories(created_at DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_tags ON agent_memories USING GIN(tags);")
            
            # 创建向量索引
            try:
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_embedding ON agent_memories USING ivfflat (embedding vector_cosine_ops);")
            except Exception as e:
                logger.warning(f"向量索引创建失败，可能需要手动创建: {str(e)}")
            
            logger.info("记忆系统数据表初始化完成")
    
    async def close(self):
        """关闭连接"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
        
        if self.pg_pool:
            await self.pg_pool.close()
        
        self.initialized = False
        logger.info("记忆系统连接已关闭")
    
    #
    # 短期记忆管理 (Redis)
    #
    
    async def save_session_memory(self, session_id: str, memory_data: Dict[str, Any], ttl: int = 3600):
        """保存会话记忆到Redis"""
        if not self.redis:
            await self.initialize()
        
        try:
            # 确保last_activity是最新的
            memory_data["last_activity"] = datetime.now().isoformat()
            
            # 序列化并保存
            await self.redis.setex(
                f"session_memory:{session_id}", 
                ttl,
                json.dumps(memory_data)
            )
            return True
        except Exception as e:
            logger.error(f"保存会话记忆失败: {str(e)}")
            return False
    
    async def get_session_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话记忆"""
        if not self.redis:
            await self.initialize()
        
        try:
            data = await self.redis.get(f"session_memory:{session_id}")
            if data:
                # 更新访问时间
                await self.redis.expire(f"session_memory:{session_id}", 3600)
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取会话记忆失败: {str(e)}")
            return None
    
    async def update_session_memory(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """更新会话记忆"""
        if not self.redis:
            await self.initialize()
        
        try:
            # 获取当前记忆
            current_memory = await self.get_session_memory(session_id)
            if not current_memory:
                return False
            
            # 更新记忆
            for key, value in updates.items():
                if key == "context" or key == "temporary_data":
                    # 对于嵌套字典，进行合并而不是替换
                    if key not in current_memory:
                        current_memory[key] = {}
                    current_memory[key].update(value)
                elif key == "conversation_history" and isinstance(value, list):
                    # 对于对话历史，追加而不是替换
                    if key not in current_memory:
                        current_memory[key] = []
                    current_memory[key].extend(value)
                else:
                    # 其他字段直接替换
                    current_memory[key] = value
            
            # 更新最后活动时间
            current_memory["last_activity"] = datetime.now().isoformat()
            
            # 保存更新后的记忆
            await self.redis.setex(
                f"session_memory:{session_id}", 
                3600,  # 1小时过期
                json.dumps(current_memory)
            )
            return True
        except Exception as e:
            logger.error(f"更新会话记忆失败: {str(e)}")
            return False
    
    async def add_conversation_entry(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        meta_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """添加对话记录到会话记忆"""
        if not self.redis:
            await self.initialize()
        
        try:
            # 创建对话条目
            entry = {
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "content": content,
"metadata": meta_info or {}
            }
            
            # 更新会话记忆
            return await self.update_session_memory(
                session_id,
                {"conversation_history": [entry]}
            )
        except Exception as e:
            logger.error(f"添加对话记录失败: {str(e)}")
            return False
    
    async def save_task_memory(self, task_id: str, task_data: Dict[str, Any], ttl: int = 7200):
        """保存任务记忆到Redis"""
        if not self.redis:
            await self.initialize()
        
        try:
            await self.redis.setex(
                f"task_memory:{task_id}", 
                ttl,
                json.dumps(task_data)
            )
            return True
        except Exception as e:
            logger.error(f"保存任务记忆失败: {str(e)}")
            return False
    
    async def get_task_memory(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务记忆"""
        if not self.redis:
            await self.initialize()
        
        try:
            data = await self.redis.get(f"task_memory:{task_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取任务记忆失败: {str(e)}")
            return None
    
    async def update_task_progress(self, task_id: str, progress: float, completed_step: Optional[str] = None) -> bool:
        """更新任务进度"""
        if not self.redis:
            await self.initialize()
        
        try:
            # 获取当前任务记忆
            task_memory = await self.get_task_memory(task_id)
            if not task_memory:
                return False
            
            # 更新进度
            task_memory["progress"] = progress
            
            # 添加已完成步骤
            if completed_step:
                if "steps_completed" not in task_memory:
                    task_memory["steps_completed"] = []
                task_memory["steps_completed"].append(completed_step)
            
            # 保存更新后的任务记忆
            await self.redis.setex(
                f"task_memory:{task_id}", 
                7200,  # 2小时过期
                json.dumps(task_memory)
            )
            return True
        except Exception as e:
            logger.error(f"更新任务进度失败: {str(e)}")
            return False
    
    #
    # 长期记忆管理 (PostgreSQL)
    #
    
    async def store_memory(
        self, 
        user_id: str, 
        memory_type: str, 
        content: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        importance_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        meta_info: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> Optional[int]:
        """存储长期记忆"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            # 计算重要性分数（如果未提供）
            if importance_score is None:
                importance_score = await self._calculate_importance_score(content)
            
            async with self.pg_pool.acquire() as conn:
                # 插入记忆
                memory_id = await conn.fetchval("""
                    INSERT INTO agent_memories 
                    (user_id, memory_type, content, embedding, importance_score, 
                     tags, meta_info, created_at, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """, 
                user_id, memory_type, json.dumps(content), embedding, importance_score,
                tags, json.dumps(meta_info) if meta_info else None, 
                datetime.now(), expires_at)
                
                logger.info(f"存储长期记忆成功，ID: {memory_id}, 类型: {memory_type}")
                return memory_id
        except Exception as e:
            logger.error(f"存储长期记忆失败: {str(e)}")
            return None
    
    async def retrieve_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """检索单个记忆"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            async with self.pg_pool.acquire() as conn:
                # 获取记忆
                row = await conn.fetchrow("""
                    SELECT id, user_id, memory_type, content, importance_score,
                           access_count, last_accessed, created_at, tags, meta_info
                    FROM agent_memories
                    WHERE id = $1 AND forgotten = FALSE
                """, memory_id)
                
                if not row:
                    return None
                
                # 更新访问计数和时间
                await conn.execute("""
                    UPDATE agent_memories
                    SET access_count = access_count + 1, last_accessed = NOW()
                    WHERE id = $1
                """, memory_id)
                
                # 记录访问日志
                await conn.execute("""
                    INSERT INTO memory_access_log (memory_id, access_type, context)
                    VALUES ($1, 'read', $2)
                """, memory_id, json.dumps({"retrieval_type": "direct"}))
                
                # 构建记忆对象
                memory = dict(row)
                memory["content"] = json.loads(memory["content"])
                if memory["meta_info"]:
                    memory["meta_info"] = json.loads(memory["meta_info"])
                
                return memory
        except Exception as e:
            logger.error(f"检索记忆失败: {str(e)}")
            return None
    
    async def retrieve_memories_by_type(
        self, 
        user_id: str, 
        memory_type: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """按类型检索记忆"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            async with self.pg_pool.acquire() as conn:
                # 获取记忆
                rows = await conn.fetch("""
                    SELECT id, user_id, memory_type, content, importance_score,
                           access_count, last_accessed, created_at, tags, meta_info
                    FROM agent_memories
                    WHERE user_id = $1 AND memory_type = $2 AND forgotten = FALSE
                    ORDER BY created_at DESC
                    LIMIT $3 OFFSET $4
                """, user_id, memory_type, limit, offset)
                
                # 构建记忆列表
                memories = []
                for row in rows:
                    memory = dict(row)
                    memory["content"] = json.loads(memory["content"])
                    if memory["meta_info"]:
                        memory["meta_info"] = json.loads(memory["meta_info"])
                    memories.append(memory)
                
                # 记录批量访问
                if memories:
                    memory_ids = [m["id"] for m in memories]
                    await conn.executemany("""
                        UPDATE agent_memories
                        SET access_count = access_count + 1, last_accessed = NOW()
                        WHERE id = $1
                    """, [(id,) for id in memory_ids])
                
                return memories
        except Exception as e:
            logger.error(f"按类型检索记忆失败: {str(e)}")
            return []
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query_context: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 5,
        time_window_days: int = 90
    ) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            # 生成查询向量
            query_embedding = await self._generate_embedding(query_context)
            if not query_embedding:
                logger.warning("无法生成查询向量，将使用基于时间的检索")
                return await self._fallback_memory_retrieval(user_id, memory_types, limit)
            
            # 构建类型过滤条件
            type_filter = ""
            if memory_types:
                type_filter = f"AND memory_type = ANY($3)"
            
            # 构建时间窗口过滤条件
            cutoff_date = datetime.now() - timedelta(days=time_window_days)
            
            async with self.pg_pool.acquire() as conn:
                # 向量相似度搜索
                query = f"""
                    SELECT 
                        id, user_id, memory_type, content, importance_score,
                        access_count, last_accessed, created_at, tags, meta_info,
                        1 - (embedding <=> $1) as similarity
                    FROM agent_memories 
                    WHERE user_id = $2 
                        {type_filter}
                        AND forgotten = FALSE
                        AND (created_at > $4 OR importance_score > 0.7)
                    ORDER BY similarity DESC
                    LIMIT $5
                """
                
                params = [query_embedding, user_id]
                if memory_types:
                    params.append(memory_types)
                params.extend([cutoff_date, limit * 2])  # 获取2倍候选
                
                rows = await conn.fetch(query, *params)
                
                # 处理结果
                candidates = []
                for row in rows:
                    memory = dict(row)
                    memory["content"] = json.loads(memory["content"])
                    if memory["meta_info"]:
                        memory["meta_info"] = json.loads(memory["meta_info"])
                    
                    # 计算时间权重
                    days_old = (datetime.now() - memory["created_at"]).days
                    time_weight = math.exp(-days_old / (time_window_days / 3))
                    
                    # 计算综合分数
                    memory["final_score"] = (
                        memory["similarity"] * 0.6 +
                        memory["importance_score"] * 0.3 +
                        time_weight * 0.1
                    )
                    
                    candidates.append(memory)
                
                # 按最终分数排序
                candidates.sort(key=lambda x: x["final_score"], reverse=True)
                
                # 确保多样性
                final_results = self._ensure_memory_diversity(candidates, limit)
                
                # 记录访问
                if final_results:
                    memory_ids = [m["id"] for m in final_results]
                    await conn.executemany("""
                        UPDATE agent_memories
                        SET access_count = access_count + 1, last_accessed = NOW()
                        WHERE id = $1
                    """, [(id,) for id in memory_ids])
                    
                    # 记录访问日志
                    await conn.executemany("""
                        INSERT INTO memory_access_log (memory_id, access_type, context)
                        VALUES ($1, 'read', $2)
                    """, [(id, json.dumps({"retrieval_type": "vector_search", "query": query_context})) for id in memory_ids])
                
                return final_results
        except Exception as e:
            logger.error(f"检索相关记忆失败: {str(e)}")
            return await self._fallback_memory_retrieval(user_id, memory_types, limit)
    
    async def _fallback_memory_retrieval(
        self, 
        user_id: str, 
        memory_types: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """基于时间和重要性的回退检索策略"""
        try:
            # 构建类型过滤条件
            type_filter = ""
            if memory_types:
                type_filter = f"AND memory_type = ANY($2)"
            
            async with self.pg_pool.acquire() as conn:
                query = f"""
                    SELECT 
                        id, user_id, memory_type, content, importance_score,
                        access_count, last_accessed, created_at, tags, meta_info
                    FROM agent_memories 
                    WHERE user_id = $1 
                        {type_filter}
                        AND forgotten = FALSE
                    ORDER BY importance_score DESC, created_at DESC
                    LIMIT $3
                """
                
                params = [user_id]
                if memory_types:
                    params.append(memory_types)
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                
                # 处理结果
                memories = []
                for row in rows:
                    memory = dict(row)
                    memory["content"] = json.loads(memory["content"])
                    if memory["meta_info"]:
                        memory["meta_info"] = json.loads(memory["meta_info"])
                    memories.append(memory)
                
                # 记录访问
                if memories:
                    memory_ids = [m["id"] for m in memories]
                    await conn.executemany("""
                        UPDATE agent_memories
                        SET access_count = access_count + 1, last_accessed = NOW()
                        WHERE id = $1
                    """, [(id,) for id in memory_ids])
                
                return memories
        except Exception as e:
            logger.error(f"回退记忆检索失败: {str(e)}")
            return []
    
    def _ensure_memory_diversity(
        self, 
        memories: List[Dict[str, Any]], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """确保记忆多样性"""
        if len(memories) <= limit:
            return memories
        
        # 按记忆类型分组
        type_groups = {}
        for memory in memories:
            memory_type = memory["memory_type"]
            if memory_type not in type_groups:
                type_groups[memory_type] = []
            type_groups[memory_type].append(memory)
        
        # 每种类型最多选择的数量
        max_per_type = max(1, limit // len(type_groups))
        
        diverse_memories = []
        remaining_slots = limit
        
        # 第一轮：每种类型选择最重要的记忆
        for memory_type, group in type_groups.items():
            if remaining_slots <= 0:
                break
                
            # 按最终分数排序
            sorted_group = sorted(
                group, 
                key=lambda x: x.get("final_score", x["importance_score"]), 
                reverse=True
            )
            
            # 选择该类型的记忆
            selected_count = min(max_per_type, len(sorted_group), remaining_slots)
            diverse_memories.extend(sorted_group[:selected_count])
            remaining_slots -= selected_count
        
        # 第二轮：填充剩余位置
        if remaining_slots > 0:
            remaining_memories = [
                m for m in memories if m not in diverse_memories
            ]
            remaining_memories.sort(
                key=lambda x: x.get("final_score", x["importance_score"]), 
                reverse=True
            )
            diverse_memories.extend(remaining_memories[:remaining_slots])
        
        return diverse_memories
    
    async def update_memory(
        self, 
        memory_id: int, 
        updates: Dict[str, Any]
    ) -> bool:
        """更新记忆"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            # 构建更新字段
            update_fields = []
            params = [memory_id]
            param_index = 2  # $1已用于memory_id
            
            for key, value in updates.items():
                if key == "content":
                    update_fields.append(f"content = ${param_index}")
                    params.append(json.dumps(value))
                    param_index += 1
                elif key == "importance_score":
                    update_fields.append(f"importance_score = ${param_index}")
                    params.append(value)
                    param_index += 1
                elif key == "tags":
                    update_fields.append(f"tags = ${param_index}")
                    params.append(value)
                    param_index += 1
                elif key == "meta_info":
                    update_fields.append(f"meta_info = ${param_index}")
                    params.append(json.dumps(value))
                    param_index += 1
                elif key == "embedding":
                    update_fields.append(f"embedding = ${param_index}")
                    params.append(value)
                    param_index += 1
            
            if not update_fields:
                logger.warning("没有提供有效的更新字段")
                return False
            
            # 执行更新
            async with self.pg_pool.acquire() as conn:
                query = f"""
                    UPDATE agent_memories
                    SET {', '.join(update_fields)}
                    WHERE id = $1
                """
                
                await conn.execute(query, *params)
                
                # 记录访问日志
                await conn.execute("""
                    INSERT INTO memory_access_log (memory_id, access_type, context)
                    VALUES ($1, 'update', $2)
                """, memory_id, json.dumps({"updated_fields": list(updates.keys())}))
                
                logger.info(f"更新记忆成功，ID: {memory_id}")
                return True
        except Exception as e:
            logger.error(f"更新记忆失败: {str(e)}")
            return False
    
    async def create_memory_association(
        self,
        source_memory_id: int,
        target_memory_id: int,
        association_type: str,
        strength: float = 0.5
    ) -> Optional[int]:
        """创建记忆关联"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            async with self.pg_pool.acquire() as conn:
                # 检查记忆是否存在
                source_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM agent_memories WHERE id = $1)",
                    source_memory_id
                )
                
                target_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM agent_memories WHERE id = $1)",
                    target_memory_id
                )
                
                if not source_exists or not target_exists:
                    logger.warning(f"创建记忆关联失败：记忆不存在，源ID: {source_memory_id}，目标ID: {target_memory_id}")
                    return None
                
                # 创建关联
                association_id = await conn.fetchval("""
                    INSERT INTO memory_associations
                    (source_memory_id, target_memory_id, association_type, strength)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, source_memory_id, target_memory_id, association_type, strength)
                
                logger.info(f"创建记忆关联成功，ID: {association_id}")
                return association_id
        except Exception as e:
            logger.error(f"创建记忆关联失败: {str(e)}")
            return None
    
    async def get_associated_memories(
        self,
        memory_id: int,
        association_type: Optional[str] = None,
        min_strength: float = 0.0
    ) -> List[Dict[str, Any]]:
        """获取关联记忆"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            # 构建类型过滤条件
            type_filter = ""
            if association_type:
                type_filter = f"AND ma.association_type = $3"
            
            async with self.pg_pool.acquire() as conn:
                query = f"""
                    SELECT 
                        am.id, am.user_id, am.memory_type, am.content, 
                        am.importance_score, am.created_at, am.tags, am.meta_info,
                        ma.association_type, ma.strength
                    FROM memory_associations ma
                    JOIN agent_memories am ON ma.target_memory_id = am.id
                    WHERE ma.source_memory_id = $1
                        AND ma.strength >= $2
                        {type_filter}
                        AND am.forgotten = FALSE
                    ORDER BY ma.strength DESC
                """
                
                params = [memory_id, min_strength]
                if association_type:
                    params.append(association_type)
                
                rows = await conn.fetch(query, *params)
                
                # 处理结果
                associated_memories = []
                for row in rows:
                    memory = dict(row)
                    memory["content"] = json.loads(memory["content"])
                    if memory["meta_info"]:
                        memory["meta_info"] = json.loads(memory["meta_info"])
                    associated_memories.append(memory)
                
                return associated_memories
        except Exception as e:
            logger.error(f"获取关联记忆失败: {str(e)}")
            return []
    
    async def forget_memory(self, memory_id: int, reason: str) -> bool:
        """执行记忆遗忘（软删除）"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            async with self.pg_pool.acquire() as conn:
                # 标记为已遗忘
                await conn.execute("""
                    UPDATE agent_memories 
                    SET 
                        forgotten = TRUE,
                        forgotten_at = NOW(),
                        forgotten_reason = $2
                    WHERE id = $1
                """, memory_id, reason)
                
                # 记录遗忘日志
                await conn.execute("""
                    INSERT INTO memory_access_log (memory_id, access_type, context)
                    VALUES ($1, 'forget', $2)
                """, memory_id, json.dumps({"reason": reason}))
                
                logger.info(f"记忆遗忘成功，ID: {memory_id}，原因: {reason}")
                return True
        except Exception as e:
            logger.error(f"记忆遗忘失败: {str(e)}")
            return False
    
    async def intelligent_forgetting(self, user_id: str):
        """智能遗忘算法"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            # 策略1: 时间衰减遗忘
            await self._time_decay_forgetting(user_id)
            
            # 策略2: 重要性阈值遗忘
            await self._importance_threshold_forgetting(user_id)
            
            # 策略3: 冗余信息遗忘
            await self._redundancy_forgetting(user_id)
            
            # 策略4: 容量限制遗忘
            await self._capacity_limit_forgetting(user_id)
            
            logger.info(f"用户 {user_id} 的智能遗忘处理完成")
            return True
        except Exception as e:
            logger.error(f"智能遗忘处理失败: {str(e)}")
            return False
    
    async def _time_decay_forgetting(self, user_id: str, max_age_days: int = 365):
        """基于时间衰减的遗忘"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        async with self.pg_pool.acquire() as conn:
            # 查找过期的低重要性记忆
            old_memories = await conn.fetch("""
                SELECT id, importance_score, created_at
                FROM agent_memories
                WHERE user_id = $1 
                    AND created_at < $2
                    AND importance_score < 0.3
                    AND forgotten = FALSE
                ORDER BY importance_score ASC, created_at ASC
                LIMIT 50
            """, user_id, cutoff_date)
            
            # 逐步遗忘
            for memory in old_memories:
                await self.forget_memory(memory["id"], "time_decay")
    
    async def _importance_threshold_forgetting(self, user_id: str, threshold: float = 0.1):
        """基于重要性阈值的遗忘"""
        async with self.pg_pool.acquire() as conn:
            # 查找低重要性记忆
            low_importance_memories = await conn.fetch("""
                SELECT id, importance_score
                FROM agent_memories
                WHERE user_id = $1 
                    AND importance_score < $2
                    AND created_at < NOW() - INTERVAL '30 days'
                    AND forgotten = FALSE
                ORDER BY importance_score ASC
                LIMIT 30
            """, user_id, threshold)
            
            # 逐步遗忘
            for memory in low_importance_memories:
                await self.forget_memory(memory["id"], "low_importance")
    
    async def _redundancy_forgetting(self, user_id: str, similarity_threshold: float = 0.95):
        """冗余信息遗忘"""
        # 查找高度相似的记忆对
        similar_pairs = await self._find_similar_memory_pairs(user_id, similarity_threshold)
        
        # 遗忘冗余记忆
        for pair in similar_pairs:
            memory1, memory2 = pair
            
            # 保留更重要的记忆
            if memory1["importance_score"] > memory2["importance_score"]:
                await self.forget_memory(memory2["id"], "redundancy")
            else:
                await self.forget_memory(memory1["id"], "redundancy")
    
    async def _capacity_limit_forgetting(self, user_id: str, max_memories: int = 1000):
        """容量限制遗忘"""
        async with self.pg_pool.acquire() as conn:
            # 检查记忆总数
            total_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM agent_memories
                WHERE user_id = $1 AND forgotten = FALSE
            """, user_id)
            
            if total_count <= max_memories:
                return
            
            # 需要遗忘的数量
            forget_count = total_count - max_memories
            
            # 查找可遗忘的低重要性记忆
            candidates = await conn.fetch("""
                SELECT id, importance_score
                FROM agent_memories
                WHERE user_id = $1 AND forgotten = FALSE
                ORDER BY importance_score ASC, last_accessed ASC NULLS FIRST
                LIMIT $2
            """, user_id, forget_count)
            
            # 逐步遗忘
            for memory in candidates:
                await self.forget_memory(memory["id"], "capacity_limit")
    
    async def _find_similar_memory_pairs(self, user_id: str, similarity_threshold: float) -> List[Tuple[Dict, Dict]]:
        """查找高度相似的记忆对"""
        similar_pairs = []
        
        try:
            async with self.pg_pool.acquire() as conn:
                # 获取所有未遗忘的记忆
                memories = await conn.fetch("""
                    SELECT id, user_id, memory_type, content, embedding, importance_score
                    FROM agent_memories
                    WHERE user_id = $1 AND forgotten = FALSE AND embedding IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 500
                """, user_id)
                
                # 转换为字典列表
                memory_dicts = []
                for row in memories:
                    memory = dict(row)
                    memory["content"] = json.loads(memory["content"])
                    memory_dicts.append(memory)
                
                # 比较记忆对
                for i in range(len(memory_dicts)):
                    for j in range(i + 1, len(memory_dicts)):
                        # 只比较相同类型的记忆
                        if memory_dicts[i]["memory_type"] != memory_dicts[j]["memory_type"]:
                            continue
                        
                        # 计算向量相似度
                        if memory_dicts[i]["embedding"] and memory_dicts[j]["embedding"]:
                            similarity = self._calculate_vector_similarity(
                                memory_dicts[i]["embedding"], 
                                memory_dicts[j]["embedding"]
                            )
                            
                            if similarity > similarity_threshold:
                                similar_pairs.append((memory_dicts[i], memory_dicts[j]))
            
            return similar_pairs
        except Exception as e:
            logger.error(f"查找相似记忆对失败: {str(e)}")
            return []
    
    def _calculate_vector_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算向量相似度（余弦相似度）"""
        try:
            # 转换为numpy数组
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            # 计算余弦相似度
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
                
            return dot_product / (norm_v1 * norm_v2)
        except Exception as e:
            logger.error(f"计算向量相似度失败: {str(e)}")
            return 0.0
    
    #
    # 记忆整合算法
    #
    
    async def consolidate_memories(self, user_id: str, consolidation_threshold: int = 3):
        """记忆整合算法"""
        if not self.pg_pool:
            await self.initialize()
        
        try:
            # 获取最近的记忆
            recent_memories = await self._get_recent_memories(user_id, days=7)
            
            if len(recent_memories) < consolidation_threshold:
                return
            
            # 按记忆类型分组
            type_groups = {}
            for memory in recent_memories:
                memory_type = memory["memory_type"]
                if memory_type not in type_groups:
                    type_groups[memory_type] = []
                type_groups[memory_type].append(memory)
            
            # 处理每种类型的记忆
            for memory_type, memories in type_groups.items():
                if len(memories) >= consolidation_threshold:
                    # 聚类分析
                    clusters = await self._cluster_memories(memories, min_cluster_size=consolidation_threshold)
                    
                    # 处理每个聚类
                    for cluster in clusters:
                        if len(cluster) >= consolidation_threshold:
                            await self._process_memory_cluster(cluster, user_id)
            
            logger.info(f"用户 {user_id} 的记忆整合处理完成")
            return True
        except Exception as e:
            logger.error(f"记忆整合处理失败: {str(e)}")
            return False
    
    async def _get_recent_memories(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近的记忆"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, user_id, memory_type, content, embedding, importance_score,
                       created_at, tags, meta_info
                FROM agent_memories
                WHERE user_id = $1 
                    AND created_at > $2
                    AND forgotten = FALSE
                ORDER BY created_at DESC
            """, user_id, cutoff_date)
            
            # 处理结果
            memories = []
            for row in rows:
                memory = dict(row)
                memory["content"] = json.loads(memory["content"])
                if memory["meta_info"]:
                    memory["meta_info"] = json.loads(memory["meta_info"])
                memories.append(memory)
            
            return memories
    
    async def _cluster_memories(self, memories: List[Dict[str, Any]], min_cluster_size: int = 3) -> List[List[Dict[str, Any]]]:
        """聚类分析记忆"""
        # 提取特征向量
        memory_vectors = []
        valid_memories = []
        
        for memory in memories:
            if memory.get("embedding") is not None:
                memory_vectors.append(memory["embedding"])
                valid_memories.append(memory)
        
        if len(valid_memories) < min_cluster_size:
            return []
        
        try:
            # 使用DBSCAN聚类
            from sklearn.cluster import DBSCAN
            import numpy as np
            
            # 转换为numpy数组
            X = np.array(memory_vectors)
            
            # DBSCAN聚类
            clustering = DBSCAN(
                eps=0.3,  # 邻域半径
                min_samples=min_cluster_size,  # 最小样本数
                metric='cosine'  # 余弦距离
            ).fit(X)
            
            # 获取聚类标签
            labels = clustering.labels_
            
            # 组织聚类结果
            clusters = {}
            for i, label in enumerate(labels):
                if label != -1:  # 忽略噪声点
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(valid_memories[i])
            
            return list(clusters.values())
        except Exception as e:
            logger.error(f"记忆聚类失败: {str(e)}")
            return []
    
    async def _process_memory_cluster(self, cluster: List[Dict[str, Any]], user_id: str):
        """处理记忆聚类"""
        try:
            # 提取共同模式
            common_pattern = self._extract_common_pattern(cluster)
            
            # 创建整合记忆
            consolidated_memory = self._create_consolidated_memory(common_pattern, cluster, user_id)
            
            # 存储整合记忆
            consolidated_id = await self.store_memory(
                user_id=user_id,
                memory_type="consolidated",
                content=consolidated_memory["content"],
                importance_score=consolidated_memory["importance_score"],
                tags=consolidated_memory["tags"],
                meta_info=consolidated_memory["meta_info"]
            )
            
            if consolidated_id:
                # 创建关联关系
                for memory in cluster:
                    await self.create_memory_association(
                        source_memory_id=memory["id"],
                        target_memory_id=consolidated_id,
                        association_type="consolidated_into",
                        strength=0.9
                    )
        except Exception as e:
            logger.error(f"处理记忆聚类失败: {str(e)}")
    
    def _extract_common_pattern(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取共同模式"""
        pattern = {
            "common_themes": [],
            "frequent_keywords": [],
            "shared_preferences": {},
            "temporal_patterns": {},
            "emotional_patterns": {}
        }
        
        # 提取内容文本
        all_content = [str(m["content"]) for m in memories]
        
        # 提取共同主题和关键词（简化实现）
        common_words = self._find_common_words(all_content)
        pattern["common_themes"] = common_words[:3]  # 前3个作为主题
        pattern["frequent_keywords"] = common_words  # 所有作为关键词
        
        # 分析时间模式
        timestamps = [m["created_at"] for m in memories]
        pattern["temporal_patterns"] = {
            "earliest": min(timestamps).isoformat(),
            "latest": max(timestamps).isoformat(),
            "count": len(timestamps)
        }
        
        # 提取标签
        all_tags = []
        for memory in memories:
            if memory.get("tags"):
                all_tags.extend(memory["tags"])
        
        if all_tags:
            # 计算标签频率
            tag_freq = {}
            for tag in all_tags:
                tag_freq[tag] = tag_freq.get(tag, 0) + 1
            
            # 选择频率最高的标签
            common_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)
            pattern["common_tags"] = [tag for tag, freq in common_tags if freq > 1]
        
        return pattern
    
    def _find_common_words(self, texts: List[str], min_count: int = 2) -> List[str]:
        """查找文本中的共同词汇"""
        # 简化实现，实际应使用NLP库进行更复杂的分析
        word_freq = {}
        
        for text in texts:
            # 简单分词
            words = text.lower().split()
            # 去重
            unique_words = set(words)
            
            for word in unique_words:
                if len(word) > 3:  # 忽略短词
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # 筛选出现次数达到阈值的词
        common_words = [word for word, freq in word_freq.items() if freq >= min_count]
        
        # 按频率排序
        common_words.sort(key=lambda w: word_freq[w], reverse=True)
        
        return common_words[:10]  # 返回前10个
    
    def _create_consolidated_memory(
        self, 
        pattern: Dict[str, Any], 
        source_memories: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """创建整合记忆"""
        # 计算整合记忆的重要性
        avg_importance = sum(m["importance_score"] for m in source_memories) / len(source_memories)
        consolidation_bonus = 0.1  # 整合记忆获得额外重要性
        
        # 提取所有标签
        all_tags = []
        for memory in source_memories:
            if memory.get("tags"):
                all_tags.extend(memory["tags"])
        
        # 去重标签
        unique_tags = list(set(all_tags))
        
        # 创建整合记忆
        consolidated_memory = {
            "memory_type": "consolidated",
            "content": {
                "pattern": pattern,
                "source_count": len(source_memories),
                "consolidation_summary": f"基于{len(source_memories)}条记忆的整合，主题包括：{', '.join(pattern['common_themes'])}",
                "time_span": {
                    "start": min(m["created_at"] for m in source_memories).isoformat(),
                    "end": max(m["created_at"] for m in source_memories).isoformat()
                }
            },
            "importance_score": min(avg_importance + consolidation_bonus, 1.0),
            "tags": unique_tags,
            "meta_info": {
                "consolidation_date": datetime.now().isoformat(),
                "source_memory_ids": [m["id"] for m in source_memories],
                "source_memory_types": list(set(m["memory_type"] for m in source_memories)),
                "user_id": user_id
            }
        }
        
        return consolidated_memory
    
    #
    # 辅助方法
    #
    
    async def _calculate_importance_score(self, content: Dict[str, Any]) -> float:
        """计算记忆重要性评分"""
        # 基础分数
        base_score = 0.5
        
        # 内容丰富度因子
        content_richness = self._calculate_content_richness(content)
        
        # 情感强度因子
        emotional_intensity = self._extract_emotional_intensity(content)
        
        # 加权计算最终分数
        importance = (
            base_score * 0.6 +
            content_richness * 0.3 +
            emotional_intensity * 0.1
        )
        
        return min(max(importance, 0.0), 1.0)
    
    def _calculate_content_richness(self, content: Dict[str, Any]) -> float:
        """计算内容丰富度"""
        richness_score = 0.0
        
        # 文本长度因子
        text_length = len(str(content))
        length_factor = min(text_length / 1000, 1.0)
        richness_score += length_factor * 0.3
        
        # 结构化数据因子
        if isinstance(content, dict):
            key_count = len(content.keys())
            structure_factor = min(key_count / 10, 1.0)
            richness_score += structure_factor * 0.3
        
        # 多媒体因子
        if 'images' in content or 'attachments' in content:
            richness_score += 0.2
        
        # 标签丰富度
        tags = content.get('tags', [])
        tag_factor = min(len(tags) / 5, 1.0)
        richness_score += tag_factor * 0.2
        
        return min(richness_score, 1.0)
    
    def _extract_emotional_intensity(self, content: Dict[str, Any]) -> float:
        """提取情感强度"""
        emotional_keywords = {
            'positive': ['喜欢', '满意', '完美', '棒', '好看', '漂亮'],
            'negative': ['不喜欢', '难看', '不合适', '失望', '糟糕'],
            'strong': ['非常', '特别', '极其', '超级', '太', '最']
        }
        
        text = str(content).lower()
        intensity = 0.0
        
        for category, keywords in emotional_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if category == 'strong':
                        intensity += 0.3
                    else:
                        intensity += 0.2
        
        return min(intensity, 1.0)
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """生成文本嵌入向量"""
        try:
            # 这里应该调用实际的嵌入模型API
            # 为简化实现，返回随机向量
            # 实际应用中应替换为真实的嵌入生成逻辑
            import numpy as np
            vector = np.random.rand(512).tolist()
            return vector
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {str(e)}")
            return None


# 创建记忆服务实例
memory_service = MemoryService()
