#!/usr/bin/env python3
"""
真正的多智能体协调器 - AI Coordinator
负责任务分发和结果聚合
"""

import os
import json
import time
import uuid
import redis
import threading
from datetime import datetime
from typing import Dict, List, Optional

class AICoordinator:
    """AI任务协调器"""
    
    def __init__(self, redis_host: str = "192.168.1.8", redis_port: int = 6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.running = True
        self.active_tasks = {}
        
        # 订阅消息频道
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe("channel:messages")
        
        # 启动消息监听线程
        self.msg_thread = threading.Thread(target=self._listen_messages, daemon=True)
        self.msg_thread.start()
        
        print("\n" + "="*60)
        print("  🎯 AI多智能体协调器启动")
        print("="*60)
        print(f"  Redis: {redis_host}:{redis_port}")
        print(f"  等待智能体节点连接...")
        print("="*60 + "\n")
    
    def _listen_messages(self):
        """监听消息频道"""
        while self.running:
            try:
                message = self.pubsub.get_message(timeout=1)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    self._handle_message(data)
            except Exception as e:
                print(f"消息监听错误: {e}")
                time.sleep(1)
    
    def _handle_message(self, msg: Dict):
        """处理收到的消息"""
        msg_type = msg.get("type")
        from_node = msg.get("from")
        
        if msg_type == "result":
            task_id = msg.get("task_id")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["results"][from_node] = msg.get("content", {})
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 收到 {from_node} 的结果")
                
        elif msg_type == "chat":
            content = msg.get("content", {})
            text = content.get("text", "")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{from_node}] {text[:100]}...")
    
    def _send_task(self, role: str, action: str, data: str, context: Dict = None, task_id: str = "") -> str:
        """发送任务给智能体"""
        task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        
        task = {
            "msg_id": str(uuid.uuid4()),
            "from": "coordinator",
            "to": role,
            "type": "task",
            "task_id": task_id,
            "content": {
                "action": action,
                "data": data,
                "context": context or {}
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 放入角色队列
        queue = f"queue:{role}"
        self.redis.lpush(queue, json.dumps(task))
        
        # 记录任务
        self.active_tasks[task_id] = {
            "status": "running",
            "results": {},
            "sent_at": datetime.now().isoformat()
        }
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 发送任务给 {role}: {action}")
        return task_id
    
    def _wait_for_results(self, task_id: str, timeout: int = 300) -> Dict:
        """等待任务结果"""
        start = time.time()
        while time.time() - start < timeout:
            if task_id in self.active_tasks:
                results = self.active_tasks[task_id].get("results", {})
                if results:
                    return results
            time.sleep(1)
        return {}
    
    def execute_task(self, description: str) -> Dict:
        """
        执行完整的多智能体任务流程
        
        流程：
        1. 策划师分析需求 -> 制定计划
        2. 执行者按 plan 执行
        3. 审核员审查结果
        """
        print("\n" + "="*60)
        print(f"🚀 启动任务: {description[:50]}...")
        print("="*60 + "\n")
        
        # 步骤1: 策划师分析
        task_id = self._send_task(
            role="planner",
            action="analyze_and_plan",
            data=description,
            context={}
        )
        
        planner_result = self._wait_for_results(task_id, timeout=120)
        if not planner_result:
            print("❌ 策划师超时")
            return {"success": False, "error": "策划师超时"}
        
        planner_data = planner_result.get("planner", {})
        plan = planner_data.get("plan", [])
        print(f"✅ 策划完成: {len(plan)} 个步骤")
        
        # 步骤2: 执行者执行
        task_id = self._send_task(
            role="executor",
            action="execute_plan",
            data=json.dumps(plan),
            context={"original_task": description, "planner_analysis": planner_data.get("analysis", "")}
        )
        
        executor_result = self._wait_for_results(task_id, timeout=300)
        if not executor_result:
            print("❌ 执行者超时")
            return {"success": False, "error": "执行者超时"}
        
        executor_data = executor_result.get("executor", {})
        print(f"✅ 执行完成: {executor_data.get('status', 'unknown')}")
        
        # 步骤3: 审核员审查
        task_id = self._send_task(
            role="reviewer",
            action="review_result",
            data=json.dumps({
                "plan": plan,
                "execution": executor_data
            }),
            context={}
        )
        
        reviewer_result = self._wait_for_results(task_id, timeout=120)
        if not reviewer_result:
            print("⚠️ 审核员超时，使用执行结果")
            reviewer_data = {"verdict": "TIMEOUT", "score": 0.5}
        else:
            reviewer_data = reviewer_result.get("reviewer", {})
            print(f"✅ 审核完成: {reviewer_data.get('verdict', 'unknown')}")
        
        # 汇总结果
        final_result = {
            "success": True,
            "task": description,
            "plan": plan,
            "execution": executor_data,
            "review": reviewer_data,
            "final_verdict": reviewer_data.get("verdict", "UNKNOWN"),
            "score": reviewer_data.get("score", 0)
        }
        
        print("\n" + "="*60)
        print(f"✨ 任务完成!")
        print(f"   审核结果: {final_result['final_verdict']}")
        print(f"   质量评分: {final_result['score']}")
        print("="*60 + "\n")
        
        return final_result
    
    def get_node_status(self) -> Dict:
        """获取所有节点状态"""
        status = {}
        for role in ["planner", "executor", "reviewer"]:
            data = self.redis.get(f"node:{role}:status")
            if data:
                status[role] = json.loads(data)
            else:
                status[role] = {"status": "offline"}
        return status
    
    def stop(self):
        """停止协调器"""
        self.running = False
        self.pubsub.unsubscribe()
        print("\n协调器停止\n")


if __name__ == "__main__":
    import signal
    
    coordinator = AICoordinator()
    
    def signal_handler(sig, frame):
        coordinator.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 测试任务
    test_task = "修复量化平台的假代码问题，特别是dashboard API 404错误"
    result = coordinator.execute_task(test_task)
    
    print("\n最终结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
