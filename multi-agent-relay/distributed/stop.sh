#!/bin/bash
# 停止所有分布式服务

if [ -f .pids ]; then
    PIDS=$(cat .pids)
    echo "🛑 正在停止服务..."
    for pid in $PIDS; do
        if kill $pid 2>/dev/null; then
            echo "  已停止 PID: $pid"
        fi
    done
    rm .pids
    echo "✅ 所有服务已停止"
else
    echo "⚠️  没有找到PID文件，尝试查找并停止相关进程..."
    pkill -f "agent_node.py" 2>/dev/null
    pkill -f "coordinator.py" 2>/dev/null
    echo "✅ 已尝试停止相关进程"
fi
