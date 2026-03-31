# 分布式多智能体架构

4台独立设备协同工作，每台运行一个 OpenClaw 智能体角色。

## 🏗️ 架构

```
┌────────────────────────────────────────────────────────────┐
│                    中控节点 (协调器)                         │
│                 http://中控IP:9000                          │
│                      ↓ 分发任务                             │
└────────────────────────────────────────────────────────────┘
        │              │              │              │
        ↓              ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   设备2      │ │   设备3      │ │   设备4      │ │   设备5      │
│  📊分析员    │ │  📋策划师    │ │  🔨执行者    │ │  ✅审核员    │
│  :9001       │ │  :9002       │ │  :9003       │ │  :9004       │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

## 📁 文件说明

| 文件 | 作用 |
|------|------|
| `agent_node.py` | 智能体节点（每台设备运行一个） |
| `coordinator.py` | 中控协调器（只在一台设备运行） |
| `config.json` | 节点配置（IP地址） |
| `test_relay.py` | 测试脚本 |
| `start_all.sh` | 本地测试启动脚本 |
| `stop.sh` | 停止脚本 |

## 🚀 部署步骤

### 第一步：配置节点IP

编辑 `config.json`，填写4台设备的实际IP：

```json
{
  "nodes": {
    "analyzer": "http://192.168.1.101:9001",
    "planner": "http://192.168.1.102:9002",
    "executor": "http://192.168.1.103:9003",
    "reviewer": "http://192.168.1.104:9004"
  }
}
```

### 第二步：在各设备上部署

**设备2（分析员）:**
```bash
# 复制 agent_node.py 和 agents/ 目录到设备2
AGENT_ROLE=analyzer AGENT_PORT=9001 python3 agent_node.py
```

**设备3（策划师）:**
```bash
AGENT_ROLE=planner AGENT_PORT=9002 python3 agent_node.py
```

**设备4（执行者）:**
```bash
AGENT_ROLE=executor AGENT_PORT=9003 python3 agent_node.py
```

**设备5（审核员）:**
```bash
AGENT_ROLE=reviewer AGENT_PORT=9004 python3 agent_node.py
```

### 第三步：启动中控

在你常用的那台设备上：
```bash
python3 coordinator.py
```

## 🧪 本地测试（单台机器）

如果你想先在一台机器上测试整个架构：

```bash
./start_all.sh
```

这会启动所有4个节点 + 协调器，使用不同的端口。

测试：
```bash
python3 test_relay.py
```

停止：
```bash
./stop.sh
```

## 📡 API 接口

### 协调器接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/nodes` | 查看节点状态 |
| POST | `/relay` | 执行接力任务 |
| GET | `/tasks` | 查看任务列表 |
| GET | `/tasks/<id>` | 查看任务详情 |

### 节点接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/info` | 节点信息 |
| POST | `/execute` | 执行任务 |

## 📝 使用示例

### 提交任务

```bash
curl -X POST http://localhost:9000/relay \
  -H "Content-Type: application/json" \
  -d '{
    "content": "设计一个个人博客网站，包含首页、文章列表和关于页面",
    "task_id": "task_001"
  }'
```

### 查看节点状态

```bash
curl http://localhost:9000/nodes
```

## 🔧 工作原理

1. **协调器**接收用户任务
2. 按顺序调用 **分析员** → **策划师** → **执行者** → **审核员**
3. 每个节点调用本地 OpenClaw 处理任务
4. 将输出传递给下一个节点
5. 最终返回完整结果

## ⚠️ 注意事项

1. 确保4台设备在同一局域网，可以互相访问
2. 防火墙需要开放 9000-9004 端口
3. 每台设备需要安装 Python3 和 requests 库
4. 节点启动后会调用本地 OpenClaw，确保配置正确

## 🐛 故障排查

**节点无法连接？**
- 检查防火墙：`sudo ufw allow 9001/tcp`
- 检查IP配置：确保 config.json 中的IP正确

**任务执行失败？**
- 检查 OpenClaw 是否正常运行
- 查看节点日志输出

**端口被占用？**
- 修改 `AGENT_PORT` 环境变量使用其他端口
