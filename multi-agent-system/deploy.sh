#!/bin/bash
# 多智能体系统部署脚本

set -e

REDIS_HOST="${REDIS_HOST:-192.168.1.8}"
ROLE="${2:-planner}"

show_help() {
    echo "使用方法:"
    echo "  ./deploy.sh coordinator           # 部署中控"
    echo "  ./deploy.sh agent <role>          # 部署智能体节点"
    echo ""
    echo "角色: planner, executor, reviewer"
}

install_redis() {
    echo "📦 安装Redis..."
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y redis-server
        sudo sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
        sudo sed -i 's/protected-mode yes/protected-mode no/' /etc/redis/redis.conf
        sudo systemctl restart redis
    elif command -v yum &> /dev/null; then
        sudo yum install -y redis
        sudo systemctl start redis
    fi
    echo "✅ Redis安装完成"
}

install_python_deps() {
    echo "📦 安装Python依赖..."
    pip3 install redis --user --break-system-packages 2>/dev/null || \
    pip3 install redis --user
    echo "✅ Python依赖安装完成"
}

deploy_coordinator() {
    echo "🚀 部署中控协调器..."
    install_redis
    install_python_deps
    
    # 创建服务文件
    cat > /tmp/coordinator.service << 'EOF'
[Unit]
Description=Multi-Agent Coordinator
After=redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/.openclaw/workspace/skills/multi-agent-system
ExecStart=/usr/bin/python3 $HOME/.openclaw/workspace/skills/multi-agent-system/coordinator.py
Restart=always

[Install]
WantedBy=default.target
EOF
    
    sed -i "s|\$HOME|$HOME|g" /tmp/coordinator.service
    sed -i "s|\$USER|$USER|g" /tmp/coordinator.service
    
    sudo cp /tmp/coordinator.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable coordinator
    
    echo "✅ 中控部署完成"
    echo "启动命令: sudo systemctl start coordinator"
}

deploy_agent() {
    local role=$1
    echo "🚀 部署智能体节点 ($role)..."
    
    install_python_deps
    
    # 创建服务文件
    cat > /tmp/agent-${role}.service << EOF
[Unit]
Description=AI Agent Node ($role)
After=network.target

[Service]
Type=simple
User=$USER
Environment="AGENT_ROLE=${role}"
Environment="REDIS_HOST=${REDIS_HOST}"
Environment="LLM_API_KEY=your-api-key-here"
WorkingDirectory=$HOME/.openclaw/workspace/skills/multi-agent-system
ExecStart=/usr/bin/python3 $HOME/.openclaw/workspace/skills/multi-agent-system/agent_node.py
Restart=always

[Install]
WantedBy=default.target
EOF
    
    sed -i "s|\$HOME|$HOME|g" /tmp/agent-${role}.service
    sed -i "s|\$USER|$USER|g" /tmp/agent-${role}.service
    
    sudo cp /tmp/agent-${role}.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable agent-${role}
    
    echo "✅ 智能体节点 ($role) 部署完成"
    echo "启动命令: sudo systemctl start agent-${role}"
}

# 主逻辑
case "$1" in
    coordinator)
        deploy_coordinator
        ;;
    agent)
        if [ -z "$2" ]; then
            echo "❌ 请指定角色: planner, executor, reviewer"
            exit 1
        fi
        deploy_agent "$2"
        ;;
    *)
        show_help
        exit 1
        ;;
esac

echo ""
echo "🎉 部署完成！"
echo "查看状态: sudo systemctl status <服务名>"
