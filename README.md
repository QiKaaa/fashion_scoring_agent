# 智能穿搭分析Agent

基于Qwen-VL-Chat API和PostgreSQL+pgvector的智能穿搭分析系统，提供多维度评分、个性化推荐和Agent长期记忆功能。

## 功能特性

- 📸 **照片上传与预处理**: 支持多种图像格式，自动优化处理
- 🔍 **智能穿搭识别**: 基于Qwen-VL-Chat API的视觉分析
- 🧠 **意图识别模块**: 自动识别用户意图，智能调用相应功能
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
- Docker & Docker Compose (推荐)

### 使用 Docker Compose 启动（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd fashion_scoring_agent
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置API密钥和其他设置
```

3. **使用启动脚本**
```bash
chmod +x start.sh
./start.sh
```
启动脚本会自动启动 PostgreSQL 和 Redis 服务，安装依赖，并启动应用。

### 手动安装

1. **克隆项目**
```bash
git clone <repository-url>
cd fashion_scoring_agent
```

2. **安装依赖**
```bash
# 使用 Poetry（推荐）
poetry install

# 或使用 pip
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和API密钥
```

4. **启动数据库服务**
```bash
# 使用 Docker Compose 启动 PostgreSQL 和 Redis
docker-compose up -d
```

5. **启动应用**
```bash
# 使用 Poetry
poetry run python -m app.main

# 或直接使用 Python
python -m app.main
```

## API文档

启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心功能

### 1. 意图识别
```python
POST /api/v1/intent/detect
```
自动识别用户意图，智能调用相应功能模块

### 2. 统一处理接口
```python
POST /api/v1/unified/process
```
一站式处理用户请求，自动识别意图并调用相应服务

### 3. 穿搭分析
```python
POST /api/v1/analysis/analyze
```
上传穿搭照片，获得详细分析和评分

### 4. 用户偏好管理
```python
GET/POST /api/v1/user/{user_id}/preferences
```
获取和更新用户偏好设置

### 5. 个性化推荐
```python
GET /api/v1/recommendations/{analysis_id}
```
基于分析结果获取个性化推荐

### 6. 相似穿搭搜索
```python
GET /api/v1/similar/{analysis_id}
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

## 数据库配置

### PostgreSQL 配置

项目使用 PostgreSQL 作为主数据库，并使用 pgvector 扩展进行向量搜索。配置参数在 `.env` 文件中：

```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fashion_scoring_agent
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fashion_scoring_agent
```

### Redis 配置

Redis 用于缓存和会话管理，配置参数在 `.env` 文件中：

```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 数据库初始化

应用启动时会自动初始化数据库表和 pgvector 扩展。如果需要手动初始化，可以执行：

```python
from app.db.init_db import init_db
import asyncio

asyncio.run(init_db())
```

## 部署

### Docker Compose 部署（推荐）
```bash
# 启动所有服务
docker-compose up -d

# 启动应用
python -m app.main
```

### 独立 Docker 部署
```bash
# 构建应用镜像
docker build -t fashion-scoring-agent .

# 运行应用容器
docker run -p 8000:8000 --network=fashion_scoring_agent_default fashion-scoring-agent
```

### 生产环境配置
- 使用 Nginx 作为反向代理
- 配置 PostgreSQL 主从复制
- 设置 Redis 集群
- 启用日志收集和监控
- 配置 HTTPS 和安全设置

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