# 多智能体分布式系统示例

## 启动协作任务

```python
from coordinator import AICoordinator

coordinator = AICoordinator()
result = coordinator.execute_task("修复量化平台的假代码问题")

print(result)
```

## 查看节点状态

```python
status = coordinator.get_node_status()
print(status)
```

## 发送自定义消息

```python
coordinator._send_message(
    to="planner",
    msg_type="task",
    content={
        "action": "analyze",
        "data": "分析任务内容"
    }
)
```
