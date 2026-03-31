# multi-agent-system

分布式多智能体协作系统

## 激活条件

用户提到以下关键词时激活：
- "多智能体"
- "分布式架构"
- "智能体协作"
- "agent node"
- "multi-agent"
- "分布式任务"

## 使用方法

### 部署分布式系统

```bash
# 在中控服务器上部署
cd ~/.openclaw/workspace/skills/multi-agent-system
./deploy.sh coordinator

# 在各智能体节点上部署
./deploy.sh agent <role>
# role可选: planner, executor, reviewer
```

### 启动协作

启动后自动通过Redis消息队列协作，支持：
- 任务自动分发
- AI自主推理
- 智能体间对话
- 结果聚合

## 文件说明

| 文件 | 说明 |
|------|------|
| `coordinator.py` | 中控协调器 |
| `agent_node.py` | 智能体节点 |
| `deploy.sh` | 部署脚本 |
| `config.json` | 节点配置 |

## 架构

```
中控 (192.168.1.8) - Redis
    ↓
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Planner │ │ Executor│ │Reviewer │
└─────────┘ └─────────┘ └─────────┘
```

## 依赖

- Python 3.10+
- Redis 6.0+
- OpenClaw

## 作者

阿呆 🤧

## 版本

v1.0.0 - 首次发布
