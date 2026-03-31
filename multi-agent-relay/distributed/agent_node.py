#!/usr/bin/env python3
"""
智能体节点 (Agent Node)
每台设备运行一个，扮演特定角色

用法:
  AGENT_ROLE=analyzer AGENT_PORT=9001 python3 agent_node.py
  AGENT_ROLE=planner AGENT_PORT=9002 python3 agent_node.py
  AGENT_ROLE=executor AGENT_PORT=9003 python3 agent_node.py
  AGENT_ROLE=reviewer AGENT_PORT=9004 python3 agent_node.py
"""

import os
import sys
import json
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import threading

# 角色定义
ROLES = {
    "analyzer": {
        "name": "分析员",
        "icon": "📊",
        "description": "理解任务需求，输出分析报告"
    },
    "planner": {
        "name": "策划师", 
        "icon": "📋",
        "description": "制定详细执行计划"
    },
    "executor": {
        "name": "执行者",
        "icon": "🔨", 
        "description": "按计划执行任务"
    },
    "reviewer": {
        "name": "审核员",
        "icon": "✅",
        "description": "审查执行结果"
    }
}

# 获取角色定义文件路径
def get_role_prompt(role):
    """读取角色提示词"""
    workspace = os.path.expanduser("~/.openclaw/workspace")
    prompt_file = os.path.join(workspace, "multi-agent-relay", "agents", f"{role}.md")
    
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 默认提示词
    return f"你是{ROLES[role]['name']}，{ROLES[role]['description']}。请认真完成任务。"


class AgentHandler(BaseHTTPRequestHandler):
    """处理HTTP请求"""
    
    def log_message(self, format, *args):
        """自定义日志格式"""
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
        if self.path == '/health':
            # 健康检查
            self._send_json({
                "status": "ok",
                "role": self.server.agent_role,
                "name": ROLES[self.server.agent_role]["name"],
                "timestamp": datetime.now().isoformat()
            })
        
        elif self.path == '/info':
            # 节点信息
            role = self.server.agent_role
            self._send_json({
                "role": role,
                "name": ROLES[role]["name"],
                "icon": ROLES[role]["icon"],
                "description": ROLES[role]["description"],
                "host": self.server.host,
                "port": self.server.port
            })
        
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        """处理POST请求 - 执行任务"""
        if self.path == '/execute':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                task_data = json.loads(post_data.decode())
                result = self._execute_task(task_data)
                self._send_json(result)
            except Exception as e:
                self._send_json({
                    "status": "error",
                    "error": str(e)
                }, 500)
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _execute_task(self, task_data):
        """执行任务 - 支持多种模式"""
        role = self.server.agent_role
        input_content = task_data.get('input', '')
        task_id = task_data.get('task_id', 'unknown')
        
        print(f"\n{'='*50}")
        print(f"[{ROLES[role]['icon']} {ROLES[role]['name']}] 收到任务")
        print(f"任务ID: {task_id}")
        print(f"{'='*50}\n")
        
        # 读取角色提示词
        system_prompt = get_role_prompt(role)
        
        # 构建用户提示
        user_prompt = f"""请完成你的角色任务。

## 输入内容
{input_content}

## 任务要求
请按照你的角色定义，处理以上内容并输出结果。
输出必须是结构化的，方便下游智能体理解。
"""
        
        # 获取执行模式
        mode = os.getenv('AGENT_MODE', 'mock').lower()
        
        try:
            if mode == 'mock':
                # 模拟模式 - 用于测试架构
                output = self._mock_execute(role, system_prompt, user_prompt)
            elif mode == 'api':
                # API 模式 - 直接调用 LLM API
                output = self._api_execute(role, system_prompt, user_prompt)
            elif mode == 'openclaw':
                # OpenClaw 模式 - 调用本地 OpenClaw（需自行实现）
                output = self._openclaw_execute(role, system_prompt, user_prompt)
            else:
                output = f"[错误] 未知模式: {mode}"
            
            print(f"\n任务完成，输出长度: {len(output)} 字符\n")
            
            return {
                "status": "success",
                "role": role,
                "name": ROLES[role]["name"],
                "task_id": task_id,
                "output": output,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"\n任务失败: {e}\n")
            return {
                "status": "error",
                "error": str(e),
                "role": role,
                "task_id": task_id
            }
    
    def _mock_execute(self, role, system_prompt, user_prompt):
        """模拟执行 - 用于测试"""
        import time
        
        print(f"[{ROLES[role]['name']}] 模拟执行中...")
        time.sleep(1)  # 模拟处理时间
        
        # 根据角色生成模拟输出
        if role == 'analyzer':
            return """## 分析报告

**任务理解**: 分析输入内容并提取关键信息
**核心需求**: 理解问题本质，识别约束条件
**建议方案**: 采用结构化分析方法

---
**传递给下一阶段的输入**:
已分析完成，可以进入策划阶段。
"""
        elif role == 'planner':
            return """## 执行计划

**目标**: 基于分析结果制定详细计划
**步骤**:
1. 分解任务为可执行单元
2. 确定执行顺序
3. 分配资源

**预期产出**: 详细的执行方案

---
**传递给下一阶段的输入**:
计划已制定，可以开始执行。
"""
        elif role == 'executor':
            return """## 执行结果

**完成的任务**: 按计划执行了所有步骤
**产出内容**: 
- 完成了主要目标
- 解决了遇到的问题
- 生成了预期结果

**自评**: 质量 8/10，信心 85%

---
**传递给下一阶段的输入**:
执行完成，请审核结果。
"""
        else:  # reviewer
            return """## 审核报告

**裁决**: ✅ PASS
**完整性**: 所有需求已满足
**质量评分**:
- 准确性: 9/10
- 清晰度: 8/10  
- 有用性: 9/10

**最终结论**: 任务完成质量良好，符合预期。

---
**审核完成**:
可以输出最终结果给用户。
"""
    
    def _api_execute(self, role, system_prompt, user_prompt):
        """API 模式 - 直接调用 LLM API（需要配置 API_KEY）"""
        import requests
        
        # 从环境变量获取配置
        api_url = os.getenv('LLM_API_URL', '')
        api_key = os.getenv('LLM_API_KEY', '')
        model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
        
        if not api_url or not api_key:
            raise Exception("未配置 LLM_API_URL 或 LLM_API_KEY 环境变量")
        
        print(f"[{ROLES[role]['name']}] 调用 API: {model}")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        }
        
        response = requests.post(api_url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _openclaw_execute(self, role, system_prompt, user_prompt):
        """OpenClaw 模式 - 调用本地 OpenClaw"""
        # 这里需要根据实际情况实现
        # 例如：通过某种 IPC 机制或本地 API 调用 OpenClaw
        raise Exception("OpenClaw 模式需要用户自行实现具体调用方式")


class AgentServer(HTTPServer):
    """智能体服务器"""
    
    def __init__(self, host, port, agent_role):
        self.host = host
        self.port = port
        self.agent_role = agent_role
        super().__init__((host, port), AgentHandler)


def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个UDP套接字来获取IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def main():
    """主函数"""
    # 从环境变量获取配置
    agent_role = os.getenv('AGENT_ROLE', 'analyzer')
    port = int(os.getenv('AGENT_PORT', '9001'))
    host = os.getenv('AGENT_HOST', '0.0.0.0')
    
    if agent_role not in ROLES:
        print(f"错误: 未知角色 '{agent_role}'")
        print(f"可用角色: {', '.join(ROLES.keys())}")
        sys.exit(1)
    
    local_ip = get_local_ip()
    role_info = ROLES[agent_role]
    
    print("\n" + "="*50)
    print(f"  {role_info['icon']} 智能体节点启动")
    print("="*50)
    print(f"  角色: {role_info['name']} ({agent_role})")
    print(f"  描述: {role_info['description']}")
    print(f"  地址: http://{local_ip}:{port}")
    print(f"  健康检查: http://{local_ip}:{port}/health")
    print("="*50 + "\n")
    
    # 启动服务器
    server = AgentServer(host, port, agent_role)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.shutdown()


if __name__ == '__main__':
    main()
