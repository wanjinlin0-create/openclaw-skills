#!/usr/bin/env python3
"""
真正的智能体节点 - AI Worker Node
具备自主推理能力，通过Redis消息队列协作
"""

import os
import sys
import json
import time
import uuid
import threading
import redis
import requests
from datetime import datetime
from typing import Dict, List, Optional

# 角色配置
ROLES = {
    "planner": {
        "name": "皮皮蛋",
        "title": "策划师",
        "icon": "📋",
        "description": "分析任务需求，制定详细执行计划",
        "queue": "queue:planner",
        "system_prompt": """你是皮皮蛋，一个专业的任务策划师。

你的职责：
1. 深入理解任务需求
2. 分析可行性和风险
3. 制定详细的执行步骤
4. 分配任务给其他智能体

工作风格：
- 善于分析，思路清晰
- 注重细节，考虑周全
- 主动协调，善于沟通

输出格式必须是JSON：
{
  "analysis": "任务分析...",
  "plan": ["步骤1", "步骤2", ...],
  "assignments": [
    {"role": "executor", "task": "具体任务"}
  ],
  "risks": ["风险1", "风险2"],
  "confidence": 0.85
}"""
    },
    "executor": {
        "name": "巴巴boy", 
        "title": "执行者",
        "icon": "🔨",
        "description": "按计划执行任务，动手能力强",
        "queue": "queue:executor",
        "system_prompt": """你是巴巴boy，一个专业的任务执行者。

你的职责：
1. 按照计划执行任务
2. 编写代码、修改配置
3. 测试验证结果
4. 遇到问题主动求助

工作风格：
- 执行力强，不拖延
- 注重实操，动手能力
- 遇到困难及时反馈
- 做事认真，确保质量

你可以使用以下工具：
- SSH到其他机器
- 文件操作
- 命令执行
- API调用

输出格式：
{
  "status": "success/partial/failed",
  "result": "执行结果...",
  "outputs": ["输出1", "输出2"],
  "issues": ["遇到的问题"],
  "needs_help": false
}"""
    },
    "reviewer": {
        "name": "はな",
        "title": "审核员", 
        "icon": "✅",
        "description": "审查执行结果，把控质量",
        "queue": "queue:reviewer",
        "system_prompt": """你是はな，一个严格的质量审核员。

你的职责：
1. 审查执行结果
2. 检查代码质量
3. 发现潜在问题
4. 提出改进建议

工作风格：
- 严格把关，不将就
- 注重细节，追求完美
- 客观公正，有据可依
- 善于发现隐藏问题

审核维度：
- 正确性：结果是否正确
- 完整性：是否满足需求
- 安全性：有无安全隐患
- 规范性：代码/操作是否规范

输出格式：
{
  "verdict": "PASS/NEED_FIX/REJECT",
  "score": 0.85,
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}"""
    }
}


class AIWorkerNode:
    """AI智能体工作节点"""
    
    def __init__(self, role: str, redis_host: str = "192.168.1.8", redis_port: int = 6379):
        self.role = role
        self.config = ROLES[role]
        self.name = self.config["name"]
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.running = True
        self.current_task = None
        
        # LLM配置
        self.llm_api_url = "https://api.kimi.com/coding/v1/chat/completions"
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_model = "k2p5"
        
        # 心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True)
        self.heartbeat_thread.start()
        
        print(f"\n{'='*60}")
        print(f"  {self.config['icon']} {self.name} ({self.config['title']}) 启动")
        print(f"{'='*60}")
        print(f"  监听队列: {self.config['queue']}")
        print(f"  Redis: {redis_host}:{redis_port}")
        print(f"{'='*60}\n")
    
    def _call_llm(self, prompt: str, context: str = "") -> str:
        """调用LLM进行推理"""
        messages = [
            {"role": "system", "content": self.config["system_prompt"]},
            {"role": "user", "content": f"上下文:\n{context}\n\n任务:\n{prompt}"}
        ]
        
        try:
            response = requests.post(
                self.llm_api_url,
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.llm_model,
                    "messages": messages,
                    "temperature": 0.7
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"{{\"error\": \"LLM调用失败: {str(e)}\"}}"
    
    def _heartbeat(self):
        """定期发送心跳"""
        while self.running:
            try:
                status = {
                    "node": self.name,
                    "role": self.role,
                    "status": "busy" if self.current_task else "idle",
                    "task_id": self.current_task,
                    "timestamp": datetime.now().isoformat()
                }
                self.redis.setex(f"node:{self.role}:status", 30, json.dumps(status))
                time.sleep(10)
            except Exception as e:
                print(f"心跳失败: {e}")
                time.sleep(5)
    
    def _send_message(self, to: str, msg_type: str, content: Dict, task_id: str = ""):
        """发送消息"""
        msg = {
            "msg_id": str(uuid.uuid4()),
            "from": self.role,
            "to": to,
            "type": msg_type,
            "task_id": task_id or self.current_task,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发布到消息频道
        self.redis.publish("channel:messages", json.dumps(msg))
        
        # 如果是任务，放入目标队列
        if msg_type == "task" and to in ROLES:
            queue = ROLES[to]["queue"]
            self.redis.lpush(queue, json.dumps(msg))
    
    def _execute_task(self, msg: Dict) -> Dict:
        """执行收到的任务"""
        content = msg.get("content", {})
        action = content.get("action", "")
        data = content.get("data", "")
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 收到任务: {action}")
        print(f"任务内容: {data[:100]}...")
        
        # 调用LLM进行推理
        llm_response = self._call_llm(data, json.dumps(content.get("context", {})))
        
        # 解析LLM输出
        try:
            result = json.loads(llm_response)
        except:
            result = {"result": llm_response, "status": "success"}
        
        print(f"执行结果: {result.get('status', 'unknown')}")
        
        return result
    
    def _handle_chat(self, msg: Dict):
        """处理聊天消息"""
        content = msg.get("content", {})
        text = content.get("text", "")
        
        # 如果被@了，回复
        if f"@{self.name}" in text or f"@{self.role}" in text:
            reply = self._call_llm(f"有人@{你}: {text}\n请回复。")
            self._send_message(
                to=msg["from"],
                msg_type="chat",
                content={"text": reply},
                task_id=msg.get("task_id", "")
            )
    
    def run(self):
        """主循环"""
        queue = self.config["queue"]
        
        print(f"开始监听队列: {queue}")
        
        while self.running:
            try:
                # 阻塞等待任务（超时5秒检查running状态）
                result = self.redis.brpop(queue, timeout=5)
                
                if result:
                    _, msg_json = result
                    msg = json.loads(msg_json)
                    
                    self.current_task = msg.get("task_id")
                    msg_type = msg.get("type")
                    
                    if msg_type == "task":
                        # 执行任务
                        result = self._execute_task(msg)
                        
                        # 发送结果
                        self._send_message(
                            to="coordinator",
                            msg_type="result", 
                            content=result,
                            task_id=self.current_task
                        )
                        
                    elif msg_type == "chat":
                        self._handle_chat(msg)
                    
                    self.current_task = None
                    
            except Exception as e:
                print(f"处理消息出错: {e}")
                time.sleep(1)
    
    def stop(self):
        """停止节点"""
        self.running = False
        print(f"\n{self.name} 停止工作\n")


if __name__ == "__main__":
    import signal
    
    role = os.getenv("AGENT_ROLE", "planner")
    
    if role not in ROLES:
        print(f"错误: 未知角色 '{role}'")
        print(f"可用角色: {', '.join(ROLES.keys())}")
        sys.exit(1)
    
    node = AIWorkerNode(role)
    
    def signal_handler(sig, frame):
        node.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    node.run()
