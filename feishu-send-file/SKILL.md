---
name: feishu-send-file
description: Send files via Feishu/Lark bot API. Use when users need to upload and send files (documents, images, archives) to Feishu users or groups through a bot. Covers credential setup, file upload, and message delivery using pywayne.lark_bot or direct API calls.
---

# 飞书文件发送指南

通过飞书机器人 API 发送文件给用户或群组。

## 前置条件

1. **飞书机器人已创建**
2. **获取到 app_id 和 app_secret**
3. **用户已添加机器人为好友**（私聊）或 **机器人在群里**（群聊）

## 快速开始

### 方法 1：使用 pywayne（推荐）

```python
from pywayne.lark_bot import LarkBot

# 初始化机器人
bot = LarkBot(
    app_id="cli_xxxxxxxxxxxxxxxx",
    app_secret="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
)

# 上传文件
file_key = bot.upload_file("/path/to/your/file.zip", file_type="stream")

# 发送给用户
bot.send_file_to_user("ou_xxxxxxxxxxxxxxxx", file_key)

# 或发送到群聊
bot.send_file_to_chat("oc_xxxxxxxxxxxxxxxx", file_key)
```

### 方法 2：使用原始 API

#### 第 1 步：获取 tenant_access_token

```bash
curl -X POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "cli_xxxxxxxxxxxxxxxx",
    "app_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }'
```

#### 第 2 步：上传文件

```bash
curl -X POST https://open.feishu.cn/open-apis/im/v1/files \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file_type=stream" \
  -F "file_name=document.pdf" \
  -F "file=@/path/to/document.pdf"
```

返回：
```json
{
  "data": {
    "file_key": "file_v3_00106_xxxxxxxxxxxxxxxx"
  }
}
```

#### 第 3 步：发送文件消息

```bash
curl -X POST https://open.feishu.cn/open-apis/im/v1/messages \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -G --data-urlencode "receive_id_type=open_id" \
  -d '{
    "receive_id": "ou_xxxxxxxxxxxxxxxx",
    "msg_type": "file",
    "content": "{\"file_key\": \"file_v3_00106_xxxxxxxxxxxxxxxx\"}"
  }'
```

## 如何获取 open_id

### 用户的 open_id

```python
# 通过邮箱或手机号查询
users = bot.get_user_info(
    emails=["user@example.com"],
    mobiles=["13800138000"]
)
open_id = users['data']['user_list'][0]['user_id']
```

### 群聊的 chat_id

```python
# 获取机器人所在的所有群
groups = bot.get_group_list()
for group in groups['data']['items']:
    print(f"群名: {group['name']}, chat_id: {group['chat_id']}")
```

## 支持的文件类型

| 文件类型 | file_type 参数 | 说明 |
|---------|---------------|------|
| 任意文件 | `stream` | 通用，任何文件都能发 |
| 图片 | `image` | 会被当作图片展示 |
| 语音 | `opus` | 需要 duration 参数 |

## 完整示例脚本

```python
#!/usr/bin/env python3
"""
飞书文件发送工具
"""
import os
import sys
from pywayne.lark_bot import LarkBot

def send_file(file_path, recipient, is_group=False):
    """
    发送文件到飞书
    
    Args:
        file_path: 本地文件路径
        recipient: open_id (用户) 或 chat_id (群聊)
        is_group: True=群聊, False=私聊
    """
    # 从环境变量读取凭证
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    if not app_id or not app_secret:
        print("错误：请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")
        sys.exit(1)
    
    # 初始化
    bot = LarkBot(app_id=app_id, app_secret=app_secret)
    
    # 检查文件
    if not os.path.exists(file_path):
        print(f"错误：文件不存在 {file_path}")
        sys.exit(1)
    
    # 上传文件
    print(f"正在上传: {file_path}")
    file_key = bot.upload_file(file_path, file_type="stream")
    print(f"上传成功，file_key: {file_key}")
    
    # 发送
    if is_group:
        print(f"发送到群聊: {recipient}")
        bot.send_file_to_chat(recipient, file_key)
    else:
        print(f"发送给用户: {recipient}")
        bot.send_file_to_user(recipient, file_key)
    
    print("发送成功！")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='发送文件到飞书')
    parser.add_argument('file', help='要发送的文件路径')
    parser.add_argument('recipient', help='用户 open_id 或群聊 chat_id')
    parser.add_argument('--group', action='store_true', help='发送到群聊')
    
    args = parser.parse_args()
    
    send_file(args.file, args.recipient, args.group)
```

## 使用方式

```bash
# 设置环境变量
export FEISHU_APP_ID="cli_xxxxxxxxxxxxxxxx"
export FEISHU_APP_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 发送给用户
python3 send_file.py document.pdf ou_xxxxxxxxxxxxxxxx

# 发送到群聊
python3 send_file.py report.zip oc_xxxxxxxxxxxxxxxx --group
```

## 常见问题

### 1. "app_id or app_secret is invalid"

检查：
- app_id 和 app_secret 是否正确
- 机器人在飞书后台是否启用

### 2. "User is not visible to the bot"

原因：用户没有添加机器人为好友
解决：让用户先在飞书里添加机器人

### 3. "Chat not found"

原因：机器人不在群里
解决：把机器人拉进群

### 4. 文件太大

飞书限制：
- 普通文件：最大 100MB
- 图片：最大 20MB

## 安全提示

⚠️ **不要把 app_secret 硬编码在代码里！**

推荐做法：
- 使用环境变量
- 或者存到 `~/.feishu-credentials` 文件，设置权限 600

```bash
# 保存凭证
echo "cli_xxxxxxxxxxxxxxxx" > ~/.feishu-app-id
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" > ~/.feishu-app-secret
chmod 600 ~/.feishu-app-id ~/.feishu-app-secret

# 读取凭证
app_id = open(os.path.expanduser("~/.feishu-app-id")).read().strip()
app_secret = open(os.path.expanduser("~/.feishu-app-secret")).read().strip()
```
