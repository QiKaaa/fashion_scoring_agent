# Agent记忆系统核心算法详解

## 1. 重要性评分算法 (Importance Scoring Algorithm)

### 1.1 算法原理
重要性评分用于确定记忆的保留价值，基于多个维度综合计算：

```python
def calculate_importance_score(memory_data: Dict) -> float:
    """
    计算记忆重要性评分
    
    评分维度：
    - 时间衰减 (20%): 新记忆权重更高
    - 访问频率 (20%): 经常访问的记忆更重要
    - 用户反馈 (20%): 用户满意度高的记忆更重要
    - 关联强度 (15%): 与其他记忆关联度高的更重要
    - 内容丰富度 (15%): 信息量大的记忆更重要
    - 情感强度 (10%): 情感色彩强烈的记忆更重要
    """
    
    # 基础分数
    base_score = 0.5
    
    # 1. 时间衰减因子 (指数衰减)
    days_since_creation = (datetime.now() - memory_data['created_at']).days
    time_factor = math.exp(-days_since_creation / 30)  # 30天半衰期
    
    # 2. 访问频率因子 (对数增长)
    access_count = memory_data.get('access_count', 0)
    access_factor = min(math.log(access_count + 1) / math.log(10), 1.0)
    
    # 3. 用户反馈因子
    satisfaction = memory_data.get('metadata', {}).get('satisfaction_score', 5)
    feedback_factor = satisfaction / 10.0
    
    # 4. 关联强度因子
    association_count = get_association_count(memory_data['id'])
    association_factor = min(association_count / 5.0, 1.0)
    
    # 5. 内容丰富度因子
    content_richness = calculate_content_richness(memory_data['content'])
    
    # 6. 情感强度因子
    emotional_intensity = extract_emotional_intensity(memory_data['content'])
    
    # 加权计算最终分数
    importance = (
        base_score * 0.0 +
        time_factor * 0.20 +
        access_factor * 0.20 +
        feedback_factor * 0.20 +
        association_factor * 0.15 +
        content_richness * 0.15 +
        emotional_intensity * 0.10
    )
    
    return min(max(importance, 0.0), 1.0)

def calculate_content_richness(content: Dict) -> float:
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

def extract_emotional_intensity(content: Dict) -> float:
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
```

## 2. 记忆检索算法 (Memory Retrieval Algorithm)

### 2.1 多阶段检索策略

```python
async def retrieve_relevant_memories(
    user_id: int,
    query_context: str,
    memory_types: List[str] = None,
    limit: int = 5,
    time_window_days: int = 90
) -> List[Dict]:
    """
    多阶段记忆检索算法
    
    阶段1: 向量相似度粗筛
    阶段2: 时间相关性过滤
    阶段3: 重要性排序
    阶段4: 多样性平衡
    阶段5: 上下文相关性精排
    """
    
    # 阶段1: 向量相似度搜索
    query_embedding = await generate_embedding(query_context)
    
    vector_candidates = await search_by_vector_similarity(
        user_id=user_id,
        query_embedding=query_embedding,
        memory_types=memory_types,
        limit=limit * 3,  # 获取3倍候选
        similarity_threshold=0.6
    )
    
    # 阶段2: 时间相关性过滤
    time_filtered = filter_by_time_relevance(
        vector_candidates, 
        time_window_days
    )
    
    # 阶段3: 重要性排序
    importance_sorted = sort_by_importance(time_filtered)
    
    # 阶段4: 多样性平衡
    diverse_results = ensure_memory_diversity(
        importance_sorted, 
        limit * 2
    )
    
    # 阶段5: 上下文相关性精排
    final_results = rerank_by_context_relevance(
        diverse_results,
        query_context,
        limit
    )
    
    return final_results

async def search_by_vector_similarity(
    user_id: int,
    query_embedding: np.ndarray,
    memory_types: List[str],
    limit: int,
    similarity_threshold: float = 0.6
) -> List[Dict]:
    """向量相似度搜索"""
    
    # 构建SQL查询
    type_filter = ""
    if memory_types:
        type_filter = f"AND memory_type = ANY('{{{','.join(memory_types)}}}')"
    
    query = f"""
    SELECT 
        id, user_id, memory_type, content, embedding,
        importance_score, created_at, last_accessed,
        (embedding <=> %s) as similarity_distance
    FROM agent_memories 
    WHERE user_id = %s 
        {type_filter}
        AND (embedding <=> %s) < %s
    ORDER BY similarity_distance ASC
    LIMIT %s
    """
    
    # 执行查询
    results = await db.fetch_all(
        query, 
        [query_embedding, user_id, query_embedding, 
         1 - similarity_threshold, limit]
    )
    
    return [dict(row) for row in results]

def filter_by_time_relevance(
    memories: List[Dict], 
    time_window_days: int
) -> List[Dict]:
    """时间相关性过滤"""
    
    cutoff_date = datetime.now() - timedelta(days=time_window_days)
    
    filtered_memories = []
    for memory in memories:
        # 计算时间权重
        memory_date = memory['created_at']
        days_old = (datetime.now() - memory_date).days
        
        # 时间权重计算 (指数衰减)
        time_weight = math.exp(-days_old / (time_window_days / 3))
        
        # 调整重要性分数
        adjusted_importance = memory['importance_score'] * time_weight
        memory['adjusted_importance'] = adjusted_importance
        
        # 保留有效记忆
        if memory_date > cutoff_date or adjusted_importance > 0.3:
            filtered_memories.append(memory)
    
    return filtered_memories

def ensure_memory_diversity(
    memories: List[Dict], 
    limit: int
) -> List[Dict]:
    """确保记忆多样性"""
    
    if len(memories) <= limit:
        return memories
    
    # 按记忆类型分组
    type_groups = {}
    for memory in memories:
        memory_type = memory['memory_type']
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
            
        # 按调整后重要性排序
        sorted_group = sorted(
            group, 
            key=lambda x: x.get('adjusted_importance', x['importance_score']), 
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
            key=lambda x: x.get('adjusted_importance', x['importance_score']), 
            reverse=True
        )
        diverse_memories.extend(remaining_memories[:remaining_slots])
    
    return diverse_memories

def rerank_by_context_relevance(
    memories: List[Dict],
    query_context: str,
    limit: int
) -> List[Dict]:
    """基于上下文相关性重新排序"""
    
    # 提取查询上下文关键词
    query_keywords = extract_keywords(query_context)
    
    for memory in memories:
        # 计算上下文匹配分数
        content_text = str(memory['content'])
        context_score = calculate_context_match_score(
            content_text, 
            query_keywords
        )
        
        # 综合分数 = 重要性 * 0.6 + 上下文相关性 * 0.4
        memory['final_score'] = (
            memory.get('adjusted_importance', memory['importance_score']) * 0.6 +
            context_score * 0.4
        )
    
    # 按最终分数排序
    memories.sort(key=lambda x: x['final_score'], reverse=True)
    
    return memories[:limit]

def calculate_context_match_score(content: str, query_keywords: List[str]) -> float:
    """计算上下文匹配分数"""
    if not query_keywords:
        return 0.5
    
    content_lower = content.lower()
    matches = 0
    
    for keyword in query_keywords:
        if keyword.lower() in content_lower:
            matches += 1
    
    return min(matches / len(query_keywords), 1.0)
```

## 3. 记忆整合算法 (Memory Consolidation Algorithm)

### 3.1 基于聚类的记忆整合

```python
async def consolidate_memories(user_id: int, consolidation_threshold: int = 3):
    """
    记忆整合算法
    
    步骤：
    1. 获取待整合记忆
    2. 特征提取和向量化
    3. 聚类分析
    4. 模式提取
    5. 创建整合记忆
    6. 更新记忆关系
    """
    
    # 步骤1: 获取最近的记忆
    recent_memories = await get_recent_memories(user_id, days=7)
    
    if len(recent_memories) < consolidation_threshold:
        return
    
    # 步骤2: 特征提取
    memory_features = []
    for memory in recent_memories:
        features = extract_memory_features(memory)
        memory_features.append(features)
    
    # 步骤3: 聚类分析
    clusters = perform_memory_clustering(
        memory_features, 
        min_cluster_size=consolidation_threshold
    )
    
    # 步骤4-6: 处理每个聚类
    for cluster_memories in clusters:
        if len(cluster_memories) >= consolidation_threshold:
            await process_memory_cluster(cluster_memories)

def extract_memory_features(memory: Dict) -> np.ndarray:
    """提取记忆特征向量"""
    features = []
    
    # 1. 语义特征 (embedding)
    semantic_features = memory.get('embedding', np.zeros(512))
    features.extend(semantic_features)
    
    # 2. 时间特征
    created_at = memory['created_at']
    hour_of_day = created_at.hour / 24.0
    day_of_week = created_at.weekday() / 7.0
    features.extend([hour_of_day, day_of_week])
    
    # 3. 类型特征 (one-hot编码)
    memory_types = ['conversation', 'preference', 'style_learning', 'context']
    type_features = [1.0 if memory['memory_type'] == t else 0.0 for t in memory_types]
    features.extend(type_features)
    
    # 4. 重要性特征
    importance = memory.get('importance_score', 0.5)
    features.append(importance)
    
    # 5. 情感特征
    emotional_intensity = extract_emotional_intensity(memory['content'])
    features.append(emotional_intensity)
    
    return np.array(features)

def perform_memory_clustering(
    features: List[np.ndarray], 
    min_cluster_size: int = 3
) -> List[List[Dict]]:
    """执行记忆聚类"""
    
    if len(features) < min_cluster_size:
        return []
    
    # 使用DBSCAN聚类算法
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    
    # 标准化特征
    scaler = StandardScaler()
    normalized_features = scaler.fit_transform(features)
    
    # DBSCAN聚类
    clustering = DBSCAN(
        eps=0.5,  # 邻域半径
        min_samples=min_cluster_size,  # 最小样本数
        metric='cosine'  # 余弦相似度
    )
    
    cluster_labels = clustering.fit_predict(normalized_features)
    
    # 组织聚类结果
    clusters = {}
    for i, label in enumerate(cluster_labels):
        if label != -1:  # 忽略噪声点
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(recent_memories[i])
    
    return list(clusters.values())

async def process_memory_cluster(cluster_memories: List[Dict]):
    """处理记忆聚类"""
    
    # 提取共同模式
    common_pattern = extract_common_pattern(cluster_memories)
    
    # 创建整合记忆
    consolidated_memory = create_consolidated_memory(common_pattern, cluster_memories)
    
    # 存储整合记忆
    consolidated_id = await store_consolidated_memory(consolidated_memory)
    
    # 创建关联关系
    for memory in cluster_memories:
        await create_memory_association(
            source_memory_id=memory['id'],
            target_memory_id=consolidated_id,
            association_type='consolidated_into',
            strength=0.9
        )
    
    # 标记原记忆为已整合
    for memory in cluster_memories:
        await mark_memory_as_consolidated(memory['id'])

def extract_common_pattern(memories: List[Dict]) -> Dict:
    """提取共同模式"""
    pattern = {
        'common_themes': [],
        'frequent_keywords': [],
        'shared_preferences': {},
        'temporal_patterns': {},
        'emotional_patterns': {}
    }
    
    # 1. 提取共同主题
    all_content = [str(m['content']) for m in memories]
    common_themes = find_common_themes(all_content)
    pattern['common_themes'] = common_themes
    
    # 2. 频繁关键词
    frequent_keywords = extract_frequent_keywords(all_content)
    pattern['frequent_keywords'] = frequent_keywords
    
    # 3. 共享偏好
    preferences = []
    for memory in memories:
        if memory['memory_type'] == 'preference':
            preferences.append(memory['content'])
    
    if preferences:
        shared_prefs = find_shared_preferences(preferences)
        pattern['shared_preferences'] = shared_prefs
    
    # 4. 时间模式
    timestamps = [m['created_at'] for m in memories]
    temporal_pattern = analyze_temporal_pattern(timestamps)
    pattern['temporal_patterns'] = temporal_pattern
    
    # 5. 情感模式
    emotional_scores = [extract_emotional_intensity(m['content']) for m in memories]
    pattern['emotional_patterns'] = {
        'average_intensity': np.mean(emotional_scores),
        'intensity_variance': np.var(emotional_scores)
    }
    
    return pattern

def create_consolidated_memory(pattern: Dict, source_memories: List[Dict]) -> Dict:
    """创建整合记忆"""
    
    # 计算整合记忆的重要性
    avg_importance = np.mean([m['importance_score'] for m in source_memories])
    consolidation_bonus = 0.1  # 整合记忆获得额外重要性
    
    consolidated_memory = {
        'memory_type': 'consolidated',
        'content': {
            'pattern': pattern,
            'source_count': len(source_memories),
            'consolidation_summary': generate_consolidation_summary(pattern),
            'time_span': {
                'start': min(m['created_at'] for m in source_memories),
                'end': max(m['created_at'] for m in source_memories)
            }
        },
        'importance_score': min(avg_importance + consolidation_bonus, 1.0),
        'tags': extract_consolidated_tags(source_memories),
        'metadata': {
            'consolidation_date': datetime.utcnow(),
            'source_memory_ids': [m['id'] for m in source_memories],
            'consolidation_confidence': calculate_consolidation_confidence(pattern)
        }
    }
    
    return consolidated_memory
```

## 4. 记忆遗忘算法 (Memory Forgetting Algorithm)

### 4.1 智能遗忘策略

```python
async def intelligent_forgetting(user_id: int):
    """
    智能遗忘算法
    
    遗忘策略：
    1. 时间衰减遗忘
    2. 重要性阈值遗忘
    3. 冗余信息遗忘
    4. 用户主动遗忘
    """
    
    # 策略1: 时间衰减遗忘
    await time_decay_forgetting(user_id)
    
    # 策略2: 重要性阈值遗忘
    await importance_threshold_forgetting(user_id)
    
    # 策略3: 冗余信息遗忘
    await redundancy_forgetting(user_id)
    
    # 策略4: 容量限制遗忘
    await capacity_limit_forgetting(user_id)

async def time_decay_forgetting(user_id: int, max_age_days: int = 365):
    """基于时间衰减的遗忘"""
    
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    # 查找过期的低重要性记忆
    old_memories = await db.fetch_all("""
        SELECT id, importance_score, created_at
        FROM agent_memories
        WHERE user_id = %s 
            AND created_at < %s
            AND importance_score < 0.3
        ORDER BY importance_score ASC, created_at ASC
    """, [user_id, cutoff_date])
    
    # 逐步遗忘
    for memory in old_memories:
        await forget_memory(memory['id'], reason='time_decay')

async def importance_threshold_forgetting(
    user_id: int, 
    threshold: float = 0.1
):
    """基于重要性阈值的遗忘"""
    
    low_importance_memories = await db.fetch_all("""
        SELECT id, importance_score
        FROM agent_memories
        WHERE user_id = %s 
            AND importance_score < %s
            AND created_at < NOW() - INTERVAL '30 days'
        ORDER BY importance_score ASC
    """, [user_id, threshold])
    
    for memory in low_importance_memories:
        await forget_memory(memory['id'], reason='low_importance')

async def redundancy_forgetting(user_id: int, similarity_threshold: float = 0.95):
    """冗余信息遗忘"""
    
    # 查找高度相似的记忆对
    similar_pairs = await find_similar_memory_pairs(
        user_id, 
        similarity_threshold
    )
    
    for pair in similar_pairs:
        memory1, memory2 = pair
        
        # 保留更重要的记忆
        if memory1['importance_score'] > memory2['importance_score']:
            await forget_memory(memory2['id'], reason='redundancy')
        else:
            await forget_memory(memory1['id'], reason='redundancy')

async def forget_memory(memory_id: int, reason: str):
    """执行记忆遗忘"""
    
    # 软删除：标记为已遗忘而不是物理删除
    await db.execute("""
        UPDATE agent_memories 
        SET 
            forgotten = TRUE,
            forgotten_at = NOW(),
            forgotten_reason = %s
        WHERE id = %s
    """, [reason, memory_id])
    
    # 记录遗忘日志
    await log_memory_forgetting(memory_id, reason)
```

这些算法确保了Agent记忆系统的智能化运作，能够有效管理记忆的存储、检索、整合和遗忘，为用户提供连贯的个性化体验。