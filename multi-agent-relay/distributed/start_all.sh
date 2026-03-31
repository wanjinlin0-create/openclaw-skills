#!/bin/bash
# 一键启动分布式多智能体架构（单节点测试模式）
# 在单台机器上启动所有4个角色 + 协调器，用于测试

echo "🚀 启动分布式多智能体架构（本地测试模式）"
echo ""

# 检查依赖
if ! python3 -c "import requests" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip3 install requests -q
fi

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 启动4个智能体节点（后台运行）
echo "🤖 启动智能体节点..."

AGENT_ROLE=analyzer AGENT_PORT=9001 python3 agent_node.py &
ANALYZER_PID=$!
echo "  📊 分析员节点启动 (PID: $ANALYZER_PID, 端口: 9001)"

AGENT_ROLE=planner AGENT_PORT=9002 python3 agent_node.py &
PLANNER_PID=$!
echo "  📋 策划师节点启动 (PID: $PLANNER_PID, 端口: 9002)"

AGENT_ROLE=executor AGENT_PORT=9003 python3 agent_node.py &
EXECUTOR_PID=$!
echo "  🔨 执行者节点启动 (PID: $EXECUTOR_PID, 端口: 9003)"

AGENT_ROLE=reviewer AGENT_PORT=9004 python3 agent_node.py &
REVIEWER_PID=$!
echo "  ✅ 审核员节点启动 (PID: $REVIEWER_PID, 端口: 9004)"

# 等待节点启动
sleep 2

# 更新配置为本地地址
cat > config.json << 'EOF'
{
  "nodes": {
    "analyzer": "http://localhost:9001",
    "planner": "http://localhost:9002",
    "executor": "http://localhost:9003",
    "reviewer": "http://localhost:9004"
  },
  "coordinator": {
    "host": "0.0.0.0",
    "port": 9000
  }
}
EOF

# 启动协调器
echo ""
echo "🎯 启动协调器..."
python3 coordinator.py &
COORDINATOR_PID=$!
echo "  协调器启动 (PID: $COORDINATOR_PID, 端口: 9000)"

# 保存PID以便后续停止
echo $ANALYZER_PID $PLANNER_PID $EXECUTOR_PID $REVIEWER_PID $COORDINATOR_PID > .pids

echo ""
echo "="*60
echo "  ✅ 所有服务已启动！"
echo "="*60
echo ""
echo "  📊 节点地址:"
echo "     • 分析员:  http://localhost:9001"
echo "     • 策划师:  http://localhost:9002"
echo "     • 执行者:  http://localhost:9003"
echo "     • 审核员:  http://localhost:9004"
echo ""
echo "  🎯 协调器地址:"
echo "     • API:     http://localhost:9000"
echo "     • 健康:    http://localhost:9000/health"
echo "     • 节点:    http://localhost:9000/nodes"
echo ""
echo "  🧪 测试命令:"
echo "     python3 test_relay.py"
echo ""
echo "  🛑 停止命令:"
echo "     ./stop.sh"
echo "="*60

# 等待用户输入
read -p "按回车键查看日志（或Ctrl+C退出）..."

# 显示日志（简单的轮询）
echo ""
echo "正在监控节点状态（按Ctrl+C停止）..."
while true; do
    clear
    echo "$(date '+%H:%M:%S') - 节点状态监控"
    echo "========================================"
    for port in 9000 9001 9002 9003 9004; do
        name="协调器"
        case $port in
            9001) name="分析员  " ;;
            9002) name="策划师  " ;;
            9003) name="执行者  " ;;
            9004) name="审核员  " ;;
        esac
        
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "✅ $name :$port 在线"
        else
            echo "❌ $name :$port 离线"
        fi
    done
    echo "========================================"
    echo "按Ctrl+C停止所有服务"
    sleep 3
done
