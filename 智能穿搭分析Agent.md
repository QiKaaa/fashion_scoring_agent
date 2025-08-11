# 智能穿搭分析Agent

## Core Features

- 照片上传与预处理

- 智能穿搭识别

- 详细描述生成

- 多维度评分系统（含预算维度）

- 用户偏好设置和风格学习

- 个性化搭配推荐

- 改进建议和替代方案

## Tech Stack

{
  "Web": {
    "arch": "api_only",
    "component": null
  },
  "language": "Python 3.9+",
  "frameworks": [
    "FastAPI",
    "LangChain",
    "Qwen-VL-Chat"
  ],
  "image_processing": [
    "Pillow",
    "OpenCV"
  ],
  "database": "SQLite",
  "vector_db": "ChromaDB",
  "package_manager": "Poetry"
}

## Design

基于Qwen-VL-Chat的本地化穿搭分析系统，采用纯API架构设计，包含图像处理、本地AI分析引擎、用户偏好学习、多维度评分系统（含预算考量）、向量相似度搜索、个性化推荐引擎和RESTful API接口，支持用户画像构建、风格学习和智能搭配推荐

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[/] 创建项目结构和虚拟环境，初始化Poetry配置文件

[ ] 安装核心依赖包：FastAPI、LangChain、Qwen-VL-Chat、ChromaDB等

[ ] 配置Qwen-VL-Chat模型和本地推理环境

[ ] 设计用户模型和偏好设置数据结构

[ ] 实现图像上传和预处理模块，支持多种格式转换和尺寸优化

[ ] 设计穿搭分析的数据模型和Pydantic schemas

[ ] 实现基于Qwen-VL-Chat的图像分析Agent，包括prompt工程和响应解析

[ ] 开发多维度评分算法，包含预算维度和个性化权重调整

[ ] 实现ChromaDB向量数据库，支持穿搭风格相似度搜索

[ ] 实现用户偏好学习和风格画像构建模块

[ ] 开发个性化搭配推荐引擎

[ ] 创建FastAPI应用和路由，实现完整的API接口

[ ] 实现SQLite数据库模型，存储用户数据、偏好和历史记录

[ ] 添加错误处理、日志记录和API文档生成

[ ] 创建测试用例和示例数据，验证系统功能

[ ] 编写项目文档和使用说明
