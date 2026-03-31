# OpenClaw Multi-Agent Distributed System

分布式多智能体协作系统 - 真正的AI工作流

## 🎯 功能

让多台运行OpenClaw的设备组成一个智能体团队，通过Redis消息队列实现：
- 任务自动分发
- AI自主推理
- 智能体间协作对话
- 无超时限制（异步消息队列）

## 🏗️ 架构

```
中控服务器 (Coordinator)
    ↓ Redis消息队列
┌─────────┐ ┌─────────┐ ┌─────────┐
│ 皮皮蛋   │ │ 巴巴boy │ │ はな     │
│(策划师)  │ │(执行者) │ │(审核员) │
└─────────┘ └─────────┘ └─────────┘
```

## 📦 包含文件

| 文件 | 说明 |
|------|------|
| `coordinator.py` | 中控协调器，负责任务分发和结果聚合 |
| `agent_node.py` | 智能体节点，具备独立LLM推理能力 |
| `deploy.sh` | 一键部署脚本 |
| `config.json` | 节点配置 |
| `examples.md` | 使用示例 |

## 🚀 快速开始

### 1. 中控部署

```bash
# 在中控服务器上
cd ~/.openclaw/workspace/skills/multi-agent-system
./deploy.sh coordinator
```

### 2. 节点部署

在每台智能体设备上：
```bash
./deploy.sh agent planner  # 皮皮蛋
./deploy.sh agent executor # 巴巴boy  
./deploy.sh agent reviewer # はな
```

### 3. 启动服务

```bash
# 中控
python3 coordinator.py

# 各节点
python3 agent_node.py
```

## 📝 使用方法

在OpenClaw中使用：
```
启动多智能体协作修复量化平台
```

## 🔧 配置

编辑 `config.json`：
```json
{
  "coordinator": "192.168.1.8",
  "nodes": {
    "planner": "192.168.1.2",
    "executor": "192.168.1.7",
    "reviewer": "192.168.1.6"
  }
}
```

## 📄 许可证

MIT
