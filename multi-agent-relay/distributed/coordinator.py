#!/usr/bin/env python3
"""
中控协调器 (Coordinator)
负责任务分发和结果收集

监听: http://0.0.0.0:9000
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# 默认节点配置（测试用）
DEFAULT_NODES = {
    "analyzer": "http://localhost:9001",
    "planner": "http://localhost:9002", 
    "executor": "http://localhost:9003",
    "reviewer": "http://localhost:9004"
}


class RelayCoordinator:
    """接力协调器"""
    
    def __init__(self, nodes_config=None):
        self.nodes = nodes_config or DEFAULT_NODES
        self.relay_chain = ["analyzer", "planner", "executor", "reviewer"]
        self.tasks = {}  # 存储任务历史
    
    def check_nodes(self):
        """检查所有节点是否在线"""
        status = {}
        for role, url in self.nodes.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status[role] = {
                        "online": True,
                        "name": data.get("name", role),
                        "url": url
                    }
                else:
                    status[role] = {"online": False, "url": url}
            except Exception as e:
                status[role] = {
                    "online": False, 
                    "url": url,
                    "error": str(e)
                }
        return status
    
    def execute_relay(self, task_content, task_id=None):
        """执行完整的接力流程"""
        if task_id is None:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n{'='*60}")
        print(f"🚀 启动接力任务: {task_id}")
        print(f"{'='*60}\n")
        
        result = {
            "task_id": task_id,
            "content": task_content,
            "start_time": datetime.now().isoformat(),
            "stages": []
        }
        
        current_input = task_content
        
        for i, role in enumerate(self.relay_chain):
            node_url = self.nodes.get(role)
            if not node_url:
                print(f"❌ 错误: 未配置 {role} 节点")
                continue
            
            print(f"\n[阶段 {i+1}/4] 发送给 {role}...")
            print(f"  URL: {node_url}")
            
            try:
                # 发送任务到节点
                response = requests.post(
                    f"{node_url}/execute",
                    json={
                        "task_id": task_id,
                        "input": current_input,
                        "stage": i + 1,
                        "total_stages": 4
                    },
                    timeout=300  # 5分钟超时
                )
                
                if response.status_code == 200:
                    stage_result = response.json()
                    result["stages"].append(stage_result)
                    
                    if stage_result.get("status") == "success":
                        current_input = stage_result.get("output", "")
                        print(f"  ✅ {role} 完成，输出长度: {len(current_input)} 字符")
                    else:
                        print(f"  ❌ {role} 执行失败: {stage_result.get('error')}")
                        result["status"] = "failed"
                        result["error_stage"] = role
                        break
                else:
                    print(f"  ❌ HTTP错误: {response.status_code}")
                    result["status"] = "failed"
                    result["error"] = f"HTTP {response.status_code}"
                    break
                    
            except Exception as e:
                print(f"  ❌ 请求失败: {e}")
                result["status"] = "failed"
                result["error"] = str(e)
                break
        
        result["end_time"] = datetime.now().isoformat()
        
        if "status" not in result:
            result["status"] = "success"
        
        self.tasks[task_id] = result
        
        print(f"\n{'='*60}")
        print(f"✨ 接力完成! 状态: {result['status']}")
        print(f"{'='*60}\n")
        
        return result


class CoordinatorHandler(BaseHTTPRequestHandler):
    """处理HTTP请求"""
    
    coordinator = None  # 类变量，共享协调器实例
    
    def log_message(self, format, *args):
        """自定义日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {format % args}")
    
    def _send_json(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/':
            # 首页信息
            self._send_json({
                "name": "多智能体分布式协调器",
                "version": "1.0",
                "nodes": self.coordinator.nodes,
                "endpoints": [
                    "GET /health - 健康检查",
                    "GET /nodes - 查看节点状态",
                    "POST /relay - 执行接力任务",
                    "GET /tasks - 查看任务历史",
                    "GET /tasks/<id> - 查看任务详情"
                ]
            })
        
        elif self.path == '/health':
            # 健康检查
            self._send_json({
                "status": "ok",
                "coordinator": "online",
                "timestamp": datetime.now().isoformat()
            })
        
        elif self.path == '/nodes':
            # 查看节点状态
            status = self.coordinator.check_nodes()
            self._send_json(status)
        
        elif self.path.startswith('/tasks/'):
            # 查看单个任务
            task_id = self.path.split('/')[-1]
            if task_id in self.coordinator.tasks:
                self._send_json(self.coordinator.tasks[task_id])
            else:
                self._send_json({"error": "Task not found"}, 404)
        
        elif self.path == '/tasks':
            # 查看所有任务
            self._send_json({
                "tasks": list(self.coordinator.tasks.keys()),
                "count": len(self.coordinator.tasks)
            })
        
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/relay':
            # 执行接力任务
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                task_data = json.loads(post_data.decode())
                content = task_data.get('content', '')
                task_id = task_data.get('task_id')
                
                if not content:
                    self._send_json({"error": "Missing content"}, 400)
                    return
                
                result = self.coordinator.execute_relay(content, task_id)
                self._send_json(result)
                
            except Exception as e:
                self._send_json({
                    "status": "error",
                    "error": str(e)
                }, 500)
        
        else:
            self._send_json({"error": "Not found"}, 404)


def main():
    """主函数"""
    # 加载配置
    config_file = os.path.expanduser("~/.openclaw/workspace/multi-agent-relay/distributed/config.json")
    
    nodes_config = DEFAULT_NODES
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                nodes_config = config.get('nodes', DEFAULT_NODES)
            print(f"✅ 已加载配置: {config_file}")
        except Exception as e:
            print(f"⚠️ 加载配置失败: {e}，使用默认配置")
    
    # 创建协调器
    coordinator = RelayCoordinator(nodes_config)
    CoordinatorHandler.coordinator = coordinator
    
    # 启动服务器
    port = int(os.getenv('COORDINATOR_PORT', '9000'))
    host = os.getenv('COORDINATOR_HOST', '0.0.0.0')
    
    server = HTTPServer((host, port), CoordinatorHandler)
    
    print("\n" + "="*60)
    print("  🎯 多智能体分布式协调器启动")
    print("="*60)
    print(f"  监听地址: http://{host}:{port}")
    print(f"\n  已配置节点:")
    for role, url in nodes_config.items():
        print(f"    • {role}: {url}")
    print("\n  API 端点:")
    print(f"    • GET  http://{host}:{port}/health   - 健康检查")
    print(f"    • GET  http://{host}:{port}/nodes    - 节点状态")
    print(f"    • POST http://{host}:{port}/relay    - 执行接力")
    print(f"    • GET  http://{host}:{port}/tasks    - 任务列表")
    print("="*60 + "\n")
    
    # 检查节点状态
    print("正在检查节点状态...")
    status = coordinator.check_nodes()
    for role, info in status.items():
        icon = "🟢" if info["online"] else "🔴"
        print(f"  {icon} {role}: {info['url']}")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭协调器...")
        server.shutdown()


if __name__ == '__main__':
    main()
