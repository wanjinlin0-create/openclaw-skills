#!/bin/bash
# 一键启动多智能体可视化平台

echo "🚀 启动多智能体可视化平台..."

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要安装 Python3"
    exit 1
fi

# 安装依赖
echo "📦 检查依赖..."
pip3 install fastapi uvicorn websockets pydantic -q 2>/dev/null || pip install fastapi uvicorn websockets pydantic -q

# 启动后端
echo "🌐 启动 Web 服务器..."
echo "   访问地址: http://localhost:8080/dashboard"
echo "   按 Ctrl+C 停止"
echo ""

cd "$(dirname "$0")/visualization/backend"
python3 main.py
