# Agent记忆系统数据结构设计

## 记忆系统架构

### 1. 记忆分层结构

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent记忆系统                            │
├─────────────────────────────────────────────────────────────┤
│  短期记忆 (Redis)           │  长期记忆 (PostgreSQL)        │
│  - 会话状态                 │  - 用户偏好演进               │
│  - 当前上下文               │  - 历史对话摘要               │
│  - 临时变量                 │  - 风格学习记录               │
│  - 任务进度                 │  - 重要事件                   │
├─────────────────────────────────────────────────────────────┤
│              工作记忆 (内存缓存)                            │
│              - 当前任务状态                                 │
│              - 活跃上下文                                   │
│              - 推理链                                       │
└─────────────────────────────────────────────────────────────┘
```

## 数据结构定义

### 1. 短期记忆数据结构 (Redis)

```python
# 会话记忆结构
SESSION_MEMORY = {
    "session_id": "sess_12345",
    "user_id": 123,
    "start_time": "2024-01-01T10:00:00Z",
    "last_activity": "2024-01-01T10:30:00Z",
    "context": {
        "current_task": "outfit_analysis",
        "conversation_stage": "analyzing",
        "user_mood": "excited",
        "preferences_mentioned": ["casual", "blue_colors"]
    },
    "temporary_data": {
        "uploaded_images": ["img_001.jpg"],
        "partial_analysis": {...},
        "user_feedback": "I like this style"
    },
    "conversation_history": [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "user",
            "content": "请分析这张穿搭照片",
            "metadata": {"image_attached": True}
        },
        {
            "timestamp": "2024-01-01T10:01:00Z",
            "role": "assistant",
            "content": "我看到您上传了一张...",
            "metadata": {"analysis_id": "ana_001"}
        }
    ]
}

# 任务状态记忆
TASK_MEMORY = {
    "task_id": "task_001",
    "task_type": "outfit_analysis",
    "status": "in_progress",
    "progress": 0.6,
    "steps_completed": ["image_upload", "preprocessing", "analysis"],
    "next_steps": ["scoring", "recommendation"],
    "context_variables": {
        "user_budget": 1000,
        "occasion": "business_meeting",
        "season": "spring"
    }
}
```

### 2. 长期记忆数据结构 (PostgreSQL)

```sql
-- 长期记忆主表
CREATE TABLE agent_memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    memory_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    embedding vector(512),
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    tags TEXT[],
    metadata JSONB
);

-- 记忆关联表（记忆之间的关系）
CREATE TABLE memory_associations (
    id SERIAL PRIMARY KEY,
    source_memory_id INTEGER REFERENCES agent_memories(id),
    target_memory_id INTEGER REFERENCES agent_memories(id),
    association_type VARCHAR(50), -- 'similar', 'causal', 'temporal', 'contradictory'
    strength FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 记忆访问日志
CREATE TABLE memory_access_log (
    id SERIAL PRIMARY KEY,
    memory_id INTEGER REFERENCES agent_memories(id),
    access_type VARCHAR(20), -- 'read', 'update', 'delete'
    context JSONB,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 具体记忆类型的数据结构

#### 3.1 对话记忆 (Conversation Memory)
```python
CONVERSATION_MEMORY = {
    "memory_type": "conversation",
    "content": {
        "conversation_id": "conv_001",
        "summary": "用户询问商务场合的穿搭建议，偏好深色系，预算1000元",
        "key_points": [
            "用户职业：金融行业",
            "偏好风格：商务正装",
            "颜色偏好：深蓝、黑色、灰色",
            "预算范围：800-1200元"
        ],
        "emotional_context": "professional, confident",
        "decisions_made": ["选择了深蓝色西装", "推荐了配套领带"],
        "unresolved_issues": ["鞋子搭配待定"]
    },
    "tags": ["business", "formal", "budget_1000", "color_preference"],
    "metadata": {
        "conversation_length": 15,
        "satisfaction_score": 8.5,
        "follow_up_needed": True
    }
}
```

#### 3.2 偏好演进记忆 (Preference Evolution Memory)
```python
PREFERENCE_MEMORY = {
    "memory_type": "preference_evolution",
    "content": {
        "preference_category": "color_preference",
        "evolution_timeline": [
            {
                "timestamp": "2024-01-01",
                "preference": ["red", "pink"],
                "confidence": 0.7,
                "context": "初次使用，表达喜欢亮色"
            },
            {
                "timestamp": "2024-02-15",
                "preference": ["blue", "navy", "red"],
                "confidence": 0.8,
                "context": "工作需要，开始接受深色系"
            },
            {
                "timestamp": "2024-03-20",
                "preference": ["navy", "gray", "blue"],
                "confidence": 0.9,
                "context": "风格成熟，偏向商务色彩"
            }
        ],
        "current_preference": ["navy", "gray", "blue"],
        "stability_score": 0.85,
        "trend_direction": "towards_professional"
    },
    "tags": ["color", "evolution", "professional_growth"],
    "metadata": {
        "change_frequency": "monthly",
        "influence_factors": ["career", "age", "lifestyle"]
    }
}
```

#### 3.3 风格学习记忆 (Style Learning Memory)
```python
STYLE_LEARNING_MEMORY = {
    "memory_type": "style_learning",
    "content": {
        "style_category": "business_casual",
        "learning_progress": {
            "initial_knowledge": 0.3,
            "current_knowledge": 0.8,
            "learning_curve": [
                {"session": 1, "score": 0.3},
                {"session": 5, "score": 0.5},
                {"session": 10, "score": 0.8}
            ]
        },
        "successful_combinations": [
            {
                "outfit": "白衬衫+深蓝西装裤+棕色皮鞋",
                "score": 9.2,
                "feedback": "非常适合商务会议"
            }
        ],
        "failed_attempts": [
            {
                "outfit": "花衬衫+正装裤",
                "score": 4.5,
                "lesson": "花纹过于复杂不适合商务场合"
            }
        ],
        "style_rules_learned": [
            "商务场合避免过于鲜艳的颜色",
            "配饰要简洁大方",
            "鞋子颜色要与腰带协调"
        ]
    },
    "tags": ["business_casual", "learning", "rules"],
    "metadata": {
        "mastery_level": "intermediate",
        "next_learning_goal": "formal_evening"
    }
}
```

#### 3.4 上下文记忆 (Context Memory)
```python
CONTEXT_MEMORY = {
    "memory_type": "context",
    "content": {
        "context_type": "seasonal_preference",
        "context_data": {
            "season": "spring",
            "weather_preferences": "轻薄透气",
            "color_adjustments": "偏向明亮色彩",
            "fabric_preferences": ["cotton", "linen", "silk"],
            "style_adaptations": "减少厚重感，增加层次"
        },
        "validity_period": {
            "start": "2024-03-01",
            "end": "2024-05-31"
        },
        "context_triggers": [
            "temperature > 15°C",
            "humidity < 70%",
            "season == 'spring'"
        ]
    },
    "tags": ["seasonal", "spring", "weather_dependent"],
    "metadata": {
        "auto_expire": True,
        "renewal_needed": True
    }
}
```

## 记忆管理算法

### 1. 重要性评分算法
```python
def calculate_importance_score(memory_data: Dict) -> float:
    """计算记忆重要性评分"""
    base_score = 0.5
    
    # 时间衰减因子
    time_factor = calculate_time_decay(memory_data['created_at'])
    
    # 访问频率因子
    access_factor = min(memory_data.get('access_count', 0) / 10, 1.0)
    
    # 用户反馈因子
    feedback_factor = memory_data.get('metadata', {}).get('satisfaction_score', 5) / 10
    
    # 关联强度因子
    association_factor = calculate_association_strength(memory_data['id'])
    
    # 内容丰富度因子
    content_factor = calculate_content_richness(memory_data['content'])
    
    importance = (
        base_score * 0.2 +
        time_factor * 0.2 +
        access_factor * 0.2 +
        feedback_factor * 0.2 +
        association_factor * 0.1 +
        content_factor * 0.1
    )
    
    return min(max(importance, 0.0), 1.0)
```

### 2. 记忆检索算法
```python
def retrieve_relevant_memories(
    user_id: int, 
    query_context: str, 
    memory_types: List[str] = None,
    limit: int = 5
) -> List[Dict]:
    """基于上下文检索相关记忆"""
    
    # 1. 生成查询向量
    query_embedding = generate_embedding(query_context)
    
    # 2. 向量相似度搜索
    vector_matches = search_by_vector_similarity(
        user_id, query_embedding, memory_types, limit * 2
    )
    
    # 3. 时间相关性过滤
    time_filtered = filter_by_time_relevance(vector_matches)
    
    # 4. 重要性排序
    importance_sorted = sort_by_importance(time_filtered)
    
    # 5. 多样性平衡
    diverse_results = ensure_diversity(importance_sorted, limit)
    
    return diverse_results
```

### 3. 记忆整合算法
```python
def consolidate_memories(user_id: int):
    """记忆整合：将相关记忆合并，提取共同模式"""
    
    # 1. 获取待整合的记忆
    recent_memories = get_recent_memories(user_id, days=7)
    
    # 2. 聚类相似记忆
    memory_clusters = cluster_similar_memories(recent_memories)
    
    # 3. 提取共同模式
    for cluster in memory_clusters:
        if len(cluster) >= 3:  # 至少3个相似记忆
            pattern = extract_common_pattern(cluster)
            
            # 4. 创建整合记忆
            consolidated_memory = create_consolidated_memory(pattern, cluster)
            
            # 5. 存储整合结果
            store_memory(consolidated_memory)
            
            # 6. 标记原记忆为已整合
            mark_memories_as_consolidated(cluster)
```

## 记忆系统配置

### Redis配置
```python
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": True,
    "max_connections": 20,
    "memory_policies": {
        "session_memory_ttl": 3600,      # 1小时
        "task_memory_ttl": 7200,         # 2小时
        "temp_data_ttl": 1800,           # 30分钟
        "max_memory_per_user": "100MB"
    }
}
```

### PostgreSQL记忆表索引
```sql
-- 性能优化索引
CREATE INDEX idx_memories_user_type ON agent_memories(user_id, memory_type);
CREATE INDEX idx_memories_importance ON agent_memories(importance_score DESC);
CREATE INDEX idx_memories_created_at ON agent_memories(created_at DESC);
CREATE INDEX idx_memories_tags ON agent_memories USING GIN(tags);
CREATE INDEX idx_memories_embedding ON agent_memories USING ivfflat (embedding vector_cosine_ops);

-- 复合索引
CREATE INDEX idx_memories_user_type_importance ON agent_memories(user_id, memory_type, importance_score DESC);
```

这个记忆系统设计提供了完整的数据结构和算法支持，能够实现Agent的长期记忆能力和上下文连贯性。