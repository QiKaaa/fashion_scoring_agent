#!/bin/bash

# 显示彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 智能穿搭分析Agent启动脚本 ===${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 检查Python是否安装
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: Python未安装，请先安装Python 3.9+${NC}"
    exit 1
fi

# 检查Poetry是否安装
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}警告: Poetry未安装，尝试使用pip安装依赖${NC}"
    HAS_POETRY=false
else
    HAS_POETRY=true
fi

# 启动数据库服务
echo -e "${GREEN}启动数据库服务...${NC}"
docker-compose up -d

# 等待数据库服务就绪
echo -e "${YELLOW}等待数据库服务就绪...${NC}"
sleep 10

# 安装依赖
echo -e "${GREEN}安装依赖...${NC}"
if [ "$HAS_POETRY" = true ]; then
    poetry install
else
    pip install -r requirements.txt
fi

# 启动应用
echo -e "${GREEN}启动应用...${NC}"
if [ "$HAS_POETRY" = true ]; then
    poetry run python -m app.main
else
    python -m app.main
fi