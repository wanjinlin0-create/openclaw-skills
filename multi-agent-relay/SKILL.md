# Multi-Agent Relay - 分布式多智能体接力系统

支持两种部署模式：本地集群 或 远程办公（公司+员工）。

## 🎯 两种架构模式

### 模式1：本地集群（所有节点在同一台机器）
```
单机运行4个节点 + 协调器
适合: 测试、演示
```

### 模式2：远程办公（公司+员工）🏢
```
NAS(中控) ←──远程连接── 4台设备(智能体)
适合: 真实分布式部署
```

---

## 🚀 快速开始

### 远程办公模式（推荐）

#### 1. 公司(NAS)部署

```bash
cd distributed
./start_company.sh
```

#### 2. 员工设备部署

在4台设备上分别运行：

```bash
# 设备1（分析员）
export AGENT_ROLE=analyzer
export AGENT_PORT=9001
export COORDINATOR_URL=http://NAS_IP:9000
./start_work.sh

# 设备2（策划师）
export AGENT_ROLE=planner
export AGENT_PORT=9002
export COORDINATOR_URL=http://NAS_IP:9000
./start_work.sh

# 设备3（执行者）
export AGENT_ROLE=executor
export AGENT_PORT=9003
export COORDINATOR_URL=http://NAS_IP:9000
./start_work.sh

# 设备4（审核员）
export AGENT_ROLE=reviewer
export AGENT_PORT=9004
export COORDINATOR_URL=http://NAS_IP:9000
./start_work.sh
```

#### 3. 提交任务

```bash
curl -X POST http://NAS_IP:9000/relay \
  -H "Content-Type: application/json" \
  -d '{"content": "设计一个个人博客网站"}'
```

---

## 📁 文件说明

```
distributed/
├── coordinator.py           # 中控协调器（NAS运行）
├── agent_node_remote.py     # 员工节点（远程办公版）
├── config.json              # 节点IP配置
├── DEPLOY_REMOTE.md         # 远程办公部署指南
├── start_company.sh         # 公司一键启动
├── start_work.sh            # 员工一键上班
└── README.md                # 本地集群部署指南
```

---

## 🔧 工作模式

| 模式 | 说明 | 配置 |
|------|------|------|
| `mock` | 模拟输出 | `export AGENT_MODE=mock` |
| `api` | 调用LLM API | `export AGENT_MODE=api` + API Key |
| `openclaw` | 本地OpenClaw | 需自行实现 |

API模式配置：
```bash
export LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
export LLM_API_KEY=your-api-key
export LLM_MODEL=moonshot-v1-8k
```

---

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/nodes` | 查看节点状态 |
| POST | `/relay` | 执行接力任务 |
| GET | `/tasks` | 任务列表 |

---

## 💡 上下班机制

- **上班**: 运行 `start_work.sh`，自动向公司注册
- **下班**: 按 Ctrl+C，优雅断开
- **请假**: 网络断开/程序崩溃，公司会标记为离线

---

## ⚠️ 注意事项

1. 确保 NAS 和 4 台设备在同一局域网
2. 防火墙开放 9000-9004 端口
3. config.json 中的 IP 要填写正确
4. J1900 建议用 API 模式（不本地跑AI）
