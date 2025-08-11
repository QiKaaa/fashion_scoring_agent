# 智能穿搭分析Agent

基于Qwen-VL-Chat API和PostgreSQL+pgvector的智能穿搭分析系统，提供多维度评分、个性化推荐和Agent长期记忆功能。

## 功能特性

- 📸 **照片上传与预处理**: 支持多种图像格式，自动优化处理
- 🔍 **智能穿搭识别**: 基于Qwen-VL-Chat API的视觉分析
- 📝 **详细描述生成**: 自然语言描述穿搭细节和风格
- 📊 **多维度评分系统**: 颜色搭配、风格协调性、场合适宜性、时尚度、个人特色、预算合理性
- 👤 **用户偏好学习**: 智能学习用户风格偏好和演进
- 💡 **个性化推荐**: 基于用户画像的搭配建议
- 🧠 **Agent长期记忆**: 上下文连贯性和历史信息调用
- 🔄 **改进建议**: 具体的穿搭优化建议

## 技术架构

### 核心技术栈
- **后端框架**: FastAPI + Python 3.9+
- **AI模型**: Qwen-VL-Chat API
- **数据库**: PostgreSQL + pgvector
- **缓存**: Redis
- **图像处理**: Pillow + OpenCV
- **依赖管理**: Poetry

### 系统架构
```
客户端调用 ←→ FastAPI Web服务 ←→ Qwen-VL-Chat API
                    ↓
               Redis缓存层
                    ↓
           PostgreSQL + pgvector
```

## 项目结构

```
fashion_scoring_agent/
├── app/                    # 应用核心代码
│   ├── api/               # API路由
│   ├── core/              # 核心业务逻辑
│   ├── models/            # 数据模型
│   ├── services/          # 服务层
│   ├── utils/             # 工具函数
│   └── ml/                # 机器学习模块
├── data/                  # 数据存储
│   ├── models/            # 预训练模型
│   ├── embeddings/        # 向量数据
│   └── images/            # 图像存储
├── tests/                 # 测试用例
├── docs/                  # 文档
├── requirements/          # 依赖文件
└── pyproject.toml         # Poetry配置
```

## 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 14+ (with pgvector extension)
- Redis 6+
- Poetry

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd fashion_scoring_agent
```

2. **安装依赖**
```bash
poetry install
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和API密钥
```

4. **初始化数据库**
```bash
poetry run alembic upgrade head
```

5. **启动服务**
```bash
poetry run uvicorn app.main:app --reload
```

## API文档

启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心功能

### 1. 穿搭分析
```python
POST /api/analyze
```
上传穿搭照片，获得详细分析和评分

### 2. 用户偏好管理
```python
GET/POST /api/user/{user_id}/preferences
```
获取和更新用户偏好设置

### 3. 个性化推荐
```python
GET /api/recommendations/{analysis_id}
```
基于分析结果获取个性化推荐

### 4. 相似穿搭搜索
```python
GET /api/similar/{analysis_id}
```
使用pgvector进行相似度搜索

## Agent记忆系统

### 记忆分层
- **短期记忆 (Redis)**: 会话状态、当前上下文
- **长期记忆 (PostgreSQL)**: 用户偏好演进、历史对话
- **工作记忆 (内存)**: 当前任务状态、推理链

### 核心算法
- **重要性评分**: 多维度智能评估记忆价值
- **记忆检索**: 五阶段精准检索相关记忆
- **记忆整合**: 基于聚类的智能记忆合并
- **智能遗忘**: 四重策略的渐进式遗忘

## 开发指南

### 代码规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 mypy 进行类型检查
- 使用 pytest 进行单元测试

### 运行测试
```bash
poetry run pytest
```

### 代码检查
```bash
poetry run black .
poetry run isort .
poetry run mypy .
```

## 部署

### Docker部署
```bash
docker build -t fashion-scoring-agent .
docker run -p 8000:8000 fashion-scoring-agent
```

### 生产环境配置
- 使用 Nginx 作为反向代理
- 配置 PostgreSQL 主从复制
- 设置 Redis 集群
- 启用日志收集和监控

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。