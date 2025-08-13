# 智能穿搭分析Agent - 技术实现方案

## 系统架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户端调用    │    │   FastAPI       │    │ Qwen-VL-Chat    │
│   (API接口)     │◄──►│   Web服务       │◄──►│   API服务       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   缓存层        │
                       │   Redis         │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   数据存储层    │
                       │PostgreSQL+pgvector│
                       └─────────────────┘
```

## 核心模块设计

### 1. 图像处理模块 (image_processor.py)
```python
class ImageProcessor:
    """图像预处理和优化"""
    
    def validate_image(self, file) -> bool:
        """验证图像格式和大小"""
        
    def preprocess_image(self, image) -> PIL.Image:
        """图像预处理：调整尺寸、优化质量、增强对比度"""
        
    def extract_features(self, image) -> dict:
        """提取基础视觉特征"""
        
    def generate_embeddings(self, image) -> np.ndarray:
        """生成图像向量嵌入用于相似度搜索"""
```

**技术实现**：
- **Pillow**: 图像格式转换、尺寸调整
- **OpenCV**: 图像增强、特征提取
- **支持格式**: JPEG, PNG, WebP
- **处理流程**: 验证 → 尺寸标准化 → 质量优化 → 特征提取 → 向量嵌入

### 2. AI分析引擎 (fashion_analyzer.py)
```python
class FashionAnalyzer:
    """基于Qwen-VL-Chat API的穿搭分析引擎"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        self.client = self._init_client()
        
    def _init_client(self):
        """初始化API客户端"""
        import requests
        return requests.Session()
    
    def analyze_outfit(self, image_url: str, user_preferences) -> AnalysisResult:
        """通过API综合分析穿搭"""
        
    def generate_description(self, analysis) -> str:
        """生成详细描述"""
        
    def calculate_scores(self, analysis, user_profile) -> dict:
        """计算多维度评分"""
        
    def _call_qwen_api(self, image_url: str, prompt: str) -> dict:
        """调用Qwen-VL-Chat API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-vl-chat-v1",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": image_url},
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        }
        
        response = self.client.post(self.base_url, headers=headers, json=payload)
        return response.json()
```

**Prompt工程设计**：
```python
ANALYSIS_PROMPT = """
作为专业时尚顾问，请分析这张穿搭照片：

1. 服装识别：
   - 上衣类型、颜色、材质
   - 下装类型、颜色、材质  
   - 鞋子、配饰详情

2. 搭配分析：
   - 颜色协调性 (1-10分)
   - 风格统一性 (1-10分)
   - 场合适宜性 (1-10分)
   - 时尚度 (1-10分)
   - 个人特色 (1-10分)
   - 预算合理性 (1-10分)

3. 用户偏好匹配：
   用户偏好: {user_preferences}
   预算范围: {budget_range}

请以JSON格式返回分析结果。
"""
```

### 3. 向量数据库模块 (vector_store.py)
```python
class VectorStore:
    """PostgreSQL + pgvector向量数据库管理"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def add_outfit_embedding(self, outfit_id: str, embedding: np.ndarray, metadata: dict):
        """添加穿搭向量嵌入到PostgreSQL"""
        query = """
        UPDATE outfit_analyses 
        SET embedding = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        self.db.execute(query, [embedding.tolist(), outfit_id])
        
    def search_similar_outfits(self, query_embedding: np.ndarray, top_k: int = 5) -> list:
        """使用pgvector搜索相似穿搭"""
        query = """
        SELECT id, analysis_result, scores, 
               (embedding <=> %s) as similarity_distance
        FROM outfit_analyses 
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s
        LIMIT %s
        """
        results = self.db.fetch_all(query, [query_embedding.tolist(), query_embedding.tolist(), top_k])
        return [dict(row) for row in results]
        
    def update_outfit_feedback(self, outfit_id: str, feedback_score: float):
        """更新穿搭反馈评分"""
        query = """
        INSERT INTO user_feedback (analysis_id, rating, created_at)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        """
        self.db.execute(query, [outfit_id, feedback_score])
```

**pgvector配置**：
- **向量维度**: 512维（基于图像特征提取）
- **相似度算法**: 余弦相似度(<=>)、欧几里得距离(<->)、内积(<#>)
- **索引类型**: IVFFlat、HNSW
- **存储格式**: PostgreSQL原生vector类型

### 4. 用户偏好学习模块 (user_profiler.py)
```python
class UserProfiler:
    """用户偏好学习和画像构建"""
    
    def build_user_profile(self, user_id, history_data) -> UserProfile:
        """构建用户画像"""
        
    def learn_preferences(self, feedback_data) -> dict:
        """从用户反馈学习偏好"""
        
    def update_style_weights(self, user_id, new_data) -> None:
        """更新个性化权重"""
        
    def find_style_clusters(self, user_embeddings) -> list:
        """发现用户风格聚类"""
```

**学习算法**：
- **协同过滤**: 基于相似用户的偏好推荐
- **内容过滤**: 基于用户历史行为分析
- **强化学习**: 根据用户反馈调整推荐策略
- **聚类分析**: K-means聚类发现用户风格偏好

### 5. 评分系统 (scoring_engine.py)
```python
class ScoringEngine:
    """多维度评分计算"""
    
    SCORE_WEIGHTS = {
        'color_harmony': 0.20,      # 颜色搭配
        'style_consistency': 0.25,  # 风格协调性
        'occasion_fit': 0.20,       # 场合适宜性
        'fashion_trend': 0.20,      # 时尚度
        'personal_style': 0.10,     # 个人特色
        'budget_efficiency': 0.05   # 预算合理性
    }
    
    def calculate_weighted_score(self, scores, user_weights) -> float:
        """计算个性化加权评分"""
        
    def generate_improvement_suggestions(self, scores) -> list:
        """生成改进建议"""
        
    def calculate_budget_score(self, items, budget_range) -> float:
        """计算预算合理性评分"""
```

### 6. 推荐引擎 (recommendation_engine.py)
```python
class RecommendationEngine:
    """个性化搭配推荐"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def recommend_alternatives(self, current_outfit, user_profile) -> list:
        """推荐替代搭配方案"""
        
    def suggest_improvements(self, analysis_result) -> list:
        """建议具体改进措施"""
        
    def find_similar_styles(self, style_features) -> list:
        """寻找相似风格参考"""
        
    def recommend_by_similarity(self, outfit_embedding) -> list:
        """基于向量相似度推荐"""
```

## 数据模型设计

### 数据库Schema (PostgreSQL + pgvector)
```sql
-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences JSONB,  -- 存储用户偏好设置
    style_profile JSONB -- 存储用户风格画像
);

-- 穿搭分析记录
CREATE TABLE outfit_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    image_path VARCHAR(255),
    image_hash VARCHAR(64),    -- 图像哈希值
    analysis_result JSONB,     -- 存储完整分析结果
    scores JSONB,              -- 存储各维度评分
    embedding vector(512),     -- 直接存储向量嵌入
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户反馈
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES outfit_analyses(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 10),
    feedback_text TEXT,
    dimension_ratings JSONB, -- 各维度的具体评分
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 风格标签
CREATE TABLE style_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    category VARCHAR(30),   -- 颜色/风格/场合等
    embedding vector(512),  -- 标签的向量表示
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量索引以提高相似度搜索性能
CREATE INDEX ON outfit_analyses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON style_tags USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- 创建其他索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_outfit_analyses_user_id ON outfit_analyses(user_id);
CREATE INDEX idx_outfit_analyses_created_at ON outfit_analyses(created_at);
CREATE INDEX idx_user_feedback_analysis_id ON user_feedback(analysis_id);
```

### Pydantic数据模型
```python
from pydantic import BaseModel
from typing import List, Optional, Dict
import numpy as np

class OutfitItem(BaseModel):
    type: str           # 服装类型
    color: str          # 颜色
    material: str       # 材质
    brand: Optional[str] # 品牌
    estimated_price: Optional[float]  # 估计价格
    style_tags: List[str] # 风格标签

class AnalysisResult(BaseModel):
    items: List[OutfitItem]
    description: str
    scores: Dict[str, float]
    suggestions: List[str]
    confidence: float
    embedding_id: Optional[str]  # 向量数据库ID

class UserPreferences(BaseModel):
    preferred_styles: List[str]
    color_preferences: List[str]
    budget_range: tuple[float, float]
    occasion_types: List[str]
    body_type: Optional[str]
    style_weights: Optional[Dict[str, float]]  # 个性化权重

class SimilarOutfit(BaseModel):
    analysis_id: int
    similarity_score: float
    thumbnail_url: str
    brief_description: str
    scores: Dict[str, float]
```

## API接口设计

### RESTful API端点
```python
# FastAPI路由设计
@app.post("/api/analyze")
async def analyze_outfit(
    file: UploadFile,
    user_id: int,
    preferences: Optional[UserPreferences] = None
) -> AnalysisResult:
    """分析穿搭照片"""

@app.get("/api/user/{user_id}/profile")
async def get_user_profile(user_id: int) -> UserProfile:
    """获取用户画像"""

@app.post("/api/user/{user_id}/preferences")
async def update_preferences(
    user_id: int, 
    preferences: UserPreferences
) -> dict:
    """更新用户偏好"""

@app.get("/api/recommendations/{analysis_id}")
async def get_recommendations(analysis_id: int) -> List[Recommendation]:
    """获取搭配推荐"""

@app.get("/api/similar/{analysis_id}")
async def get_similar_outfits(
    analysis_id: int, 
    limit: int = 10
) -> List[SimilarOutfit]:
    """获取相似穿搭"""

@app.post("/api/feedback")
async def submit_feedback(feedback: UserFeedback) -> dict:
    """提交用户反馈"""

@app.get("/api/search/style")
async def search_by_style(
    style_query: str,
    user_id: Optional[int] = None
) -> List[SimilarOutfit]:
    """按风格搜索穿搭"""
```

## Qwen-VL-Chat API集成

### API配置
```python
# API调用配置
API_CONFIG = {
    "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    "model": "qwen-vl-chat-v1",
    "max_tokens": 2048,
    "temperature": 0.7,
    "top_p": 0.9,
    "timeout": 30,
    "retry_times": 3
}

# 请求参数配置
REQUEST_CONFIG = {
    "result_format": "message",
    "incremental_output": False,
    "enable_search": False
}
```

### API调用管理器
```python
class QwenVLAPIManager:
    """Qwen-VL-Chat API调用管理器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    async def analyze_image(self, image_url: str, prompt: str) -> dict:
        """异步分析图像并返回结果"""
        payload = {
            "model": API_CONFIG["model"],
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": image_url},
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                **REQUEST_CONFIG,
                "max_tokens": API_CONFIG["max_tokens"],
                "temperature": API_CONFIG["temperature"],
                "top_p": API_CONFIG["top_p"]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_CONFIG["base_url"],
                headers=self.session.headers,
                json=payload,
                timeout=API_CONFIG["timeout"]
            ) as response:
                return await response.json()
    
    def _handle_api_error(self, response: dict) -> str:
        """处理API错误响应"""
        if "error" in response:
            error_code = response["error"].get("code", "unknown")
            error_message = response["error"].get("message", "Unknown error")
            raise APIError(f"Qwen API Error [{error_code}]: {error_message}")
        return response
```

## 性能优化策略

### 1. API调用优化
- **连接池**: 复用HTTP连接减少延迟
- **异步调用**: 使用asyncio并发处理多个请求
- **重试机制**: 智能重试失败的API调用
- **限流控制**: 避免超出API调用限制
- **缓存策略**: 缓存相似图像的分析结果

### 2. 向量搜索优化
- **pgvector索引**: 使用IVFFlat和HNSW索引提高搜索速度
- **查询优化**: 优化向量相似度查询SQL
- **批量操作**: 批量插入和更新向量数据
- **分区策略**: 按时间或用户分区存储
- **缓存热点**: 缓存热门查询结果

### 3. 图像处理优化
- **异步处理**: 使用asyncio处理图像上传和分析
- **图像压缩**: 自动压缩大尺寸图像
- **格式转换**: 统一转换为最优格式
- **CDN存储**: 使用CDN加速图像访问
- **缓存机制**: 缓存处理后的图像

### 4. 数据库优化
- **连接池**: 使用PostgreSQL连接池
- **索引优化**: 为常用查询字段添加B-tree索引
- **JSONB优化**: 为JSONB字段创建GIN索引
- **分页查询**: 大数据量查询分页处理
- **读写分离**: 配置主从复制提高读性能

## 部署架构

### 开发环境
```bash
# 项目结构
fashion_agent/
├── app/
│   ├── api/           # API路由
│   ├── core/          # 核心业务逻辑
│   ├── models/        # 数据模型
│   ├── services/      # 服务层
│   ├── utils/         # 工具函数
│   └── ml/            # 机器学习模块
├── data/
│   ├── models/        # 预训练模型
│   ├── embeddings/    # 向量数据
│   └── images/        # 图像存储
├── tests/             # 测试用例
├── docs/              # 文档
├── requirements/      # 依赖文件
└── pyproject.toml     # Poetry配置
```

### 生产环境
- **容器化**: Docker部署，支持GPU
- **负载均衡**: Nginx反向代理
- **监控**: 日志收集和性能监控
- **备份**: 定期数据备份策略
- **扩展**: 支持水平扩展

## 安全考虑

### 1. 数据安全
- **图像加密**: 用户上传图像加密存储
- **隐私保护**: 个人数据匿名化处理
- **访问控制**: JWT token认证
- **向量安全**: 向量数据加密存储

### 2. API安全
- **限流**: 防止API滥用
- **输入验证**: 严格的参数验证
- **错误处理**: 避免敏感信息泄露
- **模型安全**: 防止模型推理攻击

### 3. 模型安全
- **输入过滤**: 过滤恶意输入
- **输出检查**: 检查模型输出合规性
- **资源限制**: 限制推理资源使用
- **版本控制**: 模型版本管理和回滚

这个更新后的技术方案现在完全基于Qwen-VL-Chat本地部署，采用纯API架构，并集成了ChromaDB向量数据库用于相似度搜索和个性化推荐。