---
name: stock-market-brief
description: A股股市简报生成工具。用于生成盘前/午盘/收盘简报，包含全球市场、A股指数、板块异动、热点个股、资金流向等数据。支持发送到飞书。当用户需要获取股市数据、生成股票简报、分析板块资金流向时使用此skill。
---

# Stock Market Brief - 股市简报生成器

生成专业的A股股市简报，支持盘前、午盘、收盘三个时段。

## 功能特性

- **全球市场**：美股、港股、大宗商品
- **A股市场**：上证指数、深证成指、创业板指、沪深300
- **板块异动**：强势/弱势板块、概念板块
- **热点个股**：涨跌停榜、换手率
- **资金流向**：北向资金、主力资金、个股资金
- **自动发送**：支持发送到飞书

## 快速使用

### 生成收盘简报

```bash
python scripts/stock_brief_full.py --type close
```

### 生成并发送到飞书

```bash
python scripts/stock_brief_full.py --type close --send
```

### 生成午盘简报

```bash
python scripts/stock_brief_full.py --type noon
```

### 生成盘前简报

```bash
python scripts/stock_brief_full.py --type morning
```

## 数据源

| 数据源 | 用途 | 接口地址 |
|--------|------|----------|
| 新浪财经 | 美股/港股/A股指数 | hq.sinajs.cn |
| 东方财富 | 板块/资金流向/个股 | push2.eastmoney.com |

## 配置说明

### 飞书配置（可选）

如需发送飞书消息，修改脚本中的配置：

```python
FEISHU_APP_ID = "your-app-id"
FEISHU_APP_SECRET = "your-app-secret"
FEISHU_USER_ID = "your-open-id"
```

### 代理配置（可选）

如需代理访问海外接口，修改：

```python
PROXY_URL = 'http://127.0.0.1:9567'
```

## 数据接口详解

详见 [references/api-docs.md](references/api-docs.md)

## 注意事项

**⚠️ 重要：东方财富涨跌幅字段**

```python
# ❌ 错误 - 会导致显示0.05%而不是5%
change = item.get('f3', 0) / 100

# ✅ 正确 - f3字段已是百分比数值
change = item.get('f3', 0)
```

## 输出示例

报告包含以下内容：
- 🌍 全球市场（美股、港股、黄金原油）
- 🇨🇳 A股市场（主要指数、成交额）
- 📈 板块异动（强势/弱势板块排名）
- 🔥 热点个股（涨跌停榜）
- 💰 资金流向（北向资金、主力资金、个股资金）
- 💡 操作策略建议

## 定时任务配置

示例 Cron 配置：

```json
{
  "name": "stock-close-brief",
  "schedule": { "expr": "5 15 * * 1-5" },
  "payload": {
    "message": "python scripts/stock_brief_full.py --type close --send"
  }
}
```

## 依赖

```bash
pip install requests
```

## 许可证

MIT