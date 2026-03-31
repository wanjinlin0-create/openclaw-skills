from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from relay_system import AgentRelay

app = FastAPI(title="多智能体可视化平台")

# 存储活跃的 WebSocket 连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接的客户端"""
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# 任务存储
tasks: Dict[str, dict] = {}

class TaskRequest(BaseModel):
    content: str
    
class AgentStatus(BaseModel):
    agent: str
    status: str  # idle, working, completed
    output: Optional[str] = None
    timestamp: str

# WebSocket 连接处理
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "submit_task":
                # 提交新任务
                task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await handle_task(task_id, message.get("content", ""))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_task(task_id: str, content: str):
    """处理任务并在各阶段广播状态更新"""
    
    tasks[task_id] = {
        "id": task_id,
        "content": content,
        "status": "running",
        "stages": {},
        "start_time": datetime.now().isoformat()
    }
    
    # 广播任务开始
    await manager.broadcast({
        "type": "task_started",
        "task_id": task_id,
        "content": content
    })
    
    relay = AgentRelay()
    
    # 定义阶段处理器
    async def on_stage_complete(agent: str, output: str):
        tasks[task_id]["stages"][agent] = {
            "status": "completed",
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
        
        # 广播阶段完成
        await manager.broadcast({
            "type": "stage_completed",
            "task_id": task_id,
            "agent": agent,
            "output": output[:500] + "..." if len(output) > 500 else output
        })
    
    # 执行接力（这里需要修改 relay_system 以支持回调）
    # 简化版：直接执行并广播结果
    stages = ["analyzer", "planner", "executor", "reviewer"]
    
    for stage in stages:
        # 广播阶段开始
        await manager.broadcast({
            "type": "stage_started",
            "task_id": task_id,
            "agent": stage
        })
        
        # 模拟执行（实际应调用真实智能体）
        await asyncio.sleep(2)  # 模拟处理时间
        
        await on_stage_complete(stage, f"{stage} 的输出结果...")
    
    tasks[task_id]["status"] = "completed"
    tasks[task_id]["end_time"] = datetime.now().isoformat()
    
    # 广播任务完成
    await manager.broadcast({
        "type": "task_completed",
        "task_id": task_id,
        "result": tasks[task_id]
    })

# REST API
@app.get("/")
async def root():
    return {"message": "多智能体可视化平台 API", "version": "1.0"}

@app.get("/tasks")
async def get_tasks():
    """获取所有任务列表"""
    return list(tasks.values())

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """获取单个任务详情"""
    if task_id in tasks:
        return tasks[task_id]
    return {"error": "Task not found"}

@app.post("/tasks")
async def create_task(request: TaskRequest):
    """创建新任务（HTTP方式）"""
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 异步启动任务
    asyncio.create_task(handle_task(task_id, request.content))
    
    return {"task_id": task_id, "status": "started"}

# 挂载静态文件（前端）
try:
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")
except:
    pass  # 前端目录可能不存在

# 提供主页
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """返回可视化仪表盘 HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>多智能体可视化平台</title>
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a2e;
                color: #eee;
                min-height: 100vh;
                padding: 20px;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 { color: #00d4aa; margin-bottom: 10px; }
            .agents-container {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            .agent-card {
                background: #16213e;
                border-radius: 12px;
                padding: 20px;
                width: 200px;
                text-align: center;
                border: 2px solid #0f3460;
                transition: all 0.3s;
            }
            .agent-card.active {
                border-color: #00d4aa;
                box-shadow: 0 0 20px rgba(0, 212, 170, 0.3);
            }
            .agent-card.completed {
                border-color: #4ade80;
            }
            .agent-icon { font-size: 40px; margin-bottom: 10px; }
            .agent-name { font-weight: bold; margin-bottom: 5px; }
            .agent-status {
                font-size: 12px;
                padding: 4px 12px;
                border-radius: 20px;
                background: #0f3460;
            }
            .agent-status.working { background: #f59e0b; color: #000; }
            .agent-status.completed { background: #4ade80; color: #000; }
            .flow-container {
                background: #16213e;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .flow-line {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin: 20px 0;
            }
            .flow-arrow { color: #00d4aa; font-size: 24px; }
            .task-input {
                background: #16213e;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .task-input textarea {
                width: 100%;
                min-height: 100px;
                background: #0f3460;
                border: none;
                border-radius: 8px;
                padding: 15px;
                color: #fff;
                font-size: 14px;
                resize: vertical;
            }
            .btn {
                background: #00d4aa;
                color: #1a1a2e;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 10px;
            }
            .btn:hover { background: #00b894; }
            .logs {
                background: #16213e;
                border-radius: 12px;
                padding: 20px;
                max-height: 400px;
                overflow-y: auto;
            }
            .log-entry {
                padding: 10px;
                border-bottom: 1px solid #0f3460;
                font-family: monospace;
                font-size: 13px;
            }
            .log-entry .time { color: #888; margin-right: 10px; }
            .log-entry .agent { color: #00d4aa; margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 多智能体可视化平台</h1>
            <p>实时观察 AI 智能体的协作过程</p>
        </div>
        
        <div class="agents-container">
            <div class="agent-card" id="agent-analyzer">
                <div class="agent-icon">📊</div>
                <div class="agent-name">分析员</div>
                <div class="agent-status" id="status-analyzer">空闲</div>
            </div>
            <div style="color: #00d4aa; font-size: 24px;">→</div>
            <div class="agent-card" id="agent-planner">
                <div class="agent-icon">📋</div>
                <div class="agent-name">策划师</div>
                <div class="agent-status" id="status-planner">空闲</div>
            </div>
            <div style="color: #00d4aa; font-size: 24px;">→</div>
            <div class="agent-card" id="agent-executor">
                <div class="agent-icon">🔨</div>
                <div class="agent-name">执行者</div>
                <div class="agent-status" id="status-executor">空闲</div>
            </div>
            <div style="color: #00d4aa; font-size: 24px;">→</div>
            <div class="agent-card" id="agent-reviewer">
                <div class="agent-icon">✅</div>
                <div class="agent-name">审核员</div>
                <div class="agent-status" id="status-reviewer">空闲</div>
            </div>
        </div>
        
        <div class="task-input">
            <h3 style="margin-bottom: 15px;">📝 提交新任务</h3>
            <textarea id="taskContent" placeholder="描述你需要完成的任务...\n例如：设计一个个人博客网站，包含首页、文章列表和关于页面"></textarea>
            <button class="btn" onclick="submitTask()">开始接力</button>
        </div>
        
        <div class="logs">
            <h3 style="margin-bottom: 15px;">📋 执行日志</h3>
            <div id="logs"></div>
        </div>
        
        <script>
            let ws = null;
            
            function connect() {
                ws = new WebSocket('ws://' + window.location.host + '/ws');
                
                ws.onopen = function() {
                    addLog('系统', '已连接到服务器');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    addLog('系统', '连接已断开，5秒后重试...');
                    setTimeout(connect, 5000);
                };
            }
            
            function handleMessage(data) {
                switch(data.type) {
                    case 'task_started':
                        addLog('系统', `任务 ${data.task_id} 开始执行`);
                        break;
                    case 'stage_started':
                        setAgentStatus(data.agent, 'working');
                        addLog(data.agent, '开始工作...');
                        break;
                    case 'stage_completed':
                        setAgentStatus(data.agent, 'completed');
                        addLog(data.agent, '工作完成');
                        break;
                    case 'task_completed':
                        addLog('系统', '任务执行完成！');
                        break;
                }
            }
            
            function setAgentStatus(agent, status) {
                const card = document.getElementById('agent-' + agent);
                const statusEl = document.getElementById('status-' + agent);
                
                if (status === 'working') {
                    card.classList.add('active');
                    statusEl.textContent = '工作中...';
                    statusEl.className = 'agent-status working';
                } else if (status === 'completed') {
                    card.classList.remove('active');
                    card.classList.add('completed');
                    statusEl.textContent = '已完成';
                    statusEl.className = 'agent-status completed';
                }
            }
            
            function addLog(agent, message) {
                const logs = document.getElementById('logs');
                const time = new Date().toLocaleTimeString();
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `<span class="time">[${time}]</span><span class="agent">${agent}:</span>${message}`;
                logs.insertBefore(entry, logs.firstChild);
            }
            
            function submitTask() {
                const content = document.getElementById('taskContent').value;
                if (!content.trim()) {
                    alert('请输入任务内容');
                    return;
                }
                
                // 重置状态
                ['analyzer', 'planner', 'executor', 'reviewer'].forEach(agent => {
                    const card = document.getElementById('agent-' + agent);
                    card.classList.remove('active', 'completed');
                    const statusEl = document.getElementById('status-' + agent);
                    statusEl.textContent = '空闲';
                    statusEl.className = 'agent-status';
                });
                
                ws.send(JSON.stringify({
                    type: 'submit_task',
                    content: content
                }));
                
                addLog('系统', '任务已提交');
            }
            
            connect();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
