# API接口文档

## 一、新浪财经接口

### 1.1 美股指数

**接口地址：**
```
https://hq.sinajs.cn/list=int_dji,int_nasdaq,int_sp500
```

**返回格式：**
```javascript
var hq_str_int_dji="道琼斯,46247.29,299.97,0.65";
var hq_str_int_nasdaq="纳斯达克,22484.07,99.37,0.44";
var hq_str_int_sp500="标普500,6643.70,38.98,0.59";
```

**字段说明：**
| 位置 | 字段 | 说明 |
|------|------|------|
| p[0] | name | 指数名称 |
| p[1] | price | 当前价格 |
| p[2] | change | 涨跌额 |
| p[3] | change_pct | 涨跌幅% |

---

### 1.2 A股指数

**接口地址：**
```
https://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006,s_sh000300
```

**代码映射：**
| 代码 | 名称 |
|------|------|
| sh000001 | 上证指数 |
| sz399001 | 深证成指 |
| sz399006 | 创业板指 |
| sh000300 | 沪深300 |

**返回格式：**
```javascript
var hq_str_s_sh000001="上证指数,4024.23,-38.75,-0.95";
```

---

### 1.3 港股指数

**接口地址：**
```
https://hq.sinajs.cn/list=rt_hkHSI,rt_hkHSTECH,rt_hkHSCEI
```

**代码映射：**
| 代码 | 名称 |
|------|------|
| hkHSI | 恒生指数 |
| hkHSTECH | 恒生科技 |
| hkHSCEI | 国企指数 |

---

### 1.4 中概股ADR

**接口地址：**
```
https://hq.sinajs.cn/list=gb_baba,gb_pdd,gb_jd,gb_bidu
```

**代码映射：**
| 代码 | 名称 |
|------|------|
| gb_baba | 阿里巴巴 |
| gb_pdd | 拼多多 |
| gb_jd | 京东 |
| gb_bidu | 百度 |

---

## 二、东方财富接口

### 2.1 板块数据

**接口地址：**
```
https://push2.eastmoney.com/api/qt/clist/get
```

**请求参数：**
| 参数 | 值 | 说明 |
|------|-----|------|
| pn | 1 | 页码 |
| pz | 20 | 每页条数 |
| po | 1 | 排序方向（1=降序，0=升序） |
| fid | f3 | 排序字段 |
| fs | m:90+t:2 | 板块分类 |
| fields | f12,f14,f3,f20 | 返回字段 |

**返回字段：**
| 字段 | 说明 | 示例 |
|------|------|------|
| f12 | 板块代码 | 代码 |
| f14 | 板块名称 | 光伏设备 |
| **f3** | **涨跌幅** | **4.51（表示4.51%）** |
| f20 | 成交额 | 金额（元）|

**⚠️ 重要提示：**
```python
# ❌ 错误用法
change = item.get('f3', 0) / 100  # 会显示0.05%

# ✅ 正确用法
change = item.get('f3', 0)        # 正确显示4.51%
```

---

### 2.2 资金流向

**主力资金：**
```
fid=f62&fields=f14,f62
```

**字段说明：**
| 字段 | 说明 | 单位 |
|------|------|------|
| f14 | 行业名称 | - |
| f62 | 主力资金净流入 | 元（需÷100000000转亿元）|

---

### 2.3 热点个股

**涨幅榜：**
```
fid=f3&po=1&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23
```

**跌幅榜：**
```
fid=f3&po=0&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23
```

**参数说明：**
| 参数 | 说明 |
|------|------|
| fs=m:0+t:6 | 沪A主板 |
| fs=m:0+t:13 | 沪A科创板 |
| fs=m:1+t:2 | 深A主板 |
| fs=m:1+t:23 | 深A创业板 |

---

### 2.4 涨停分析

**接口地址：**
```
https://push2ex.eastmoney.com/getTopicZDT
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| ztNum | 涨停数 |
| dtNum | 跌停数 |
| ztZbNum | 炸板数 |
| ztFirstNum | 首板数 |
| ztLbNum | 连板数 |

---

### 2.5 市场估值

**接口地址：**
```
https://push2.eastmoney.com/api/qt/ulist.np/get
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| f33 | 市盈率PE |
| f34 | 市净率PB |

---

## 三、飞书API

### 3.1 获取Token

**接口地址：**
```
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
```

**请求体：**
```json
{
  "app_id": "cli_xxx",
  "app_secret": "xxx"
}
```

**返回：**
```json
{
  "code": 0,
  "tenant_access_token": "t-xxx",
  "expire": 7200
}
```

---

### 3.2 发送消息

**接口地址：**
```
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id
```

**请求头：**
```
Authorization: Bearer {tenant_access_token}
Content-Type: application/json
```

**请求体：**
```json
{
  "receive_id": "ou_xxx",
  "msg_type": "text",
  "content": "{\"text\": \"消息内容\"}"
}
```

---

## 四、常见问题

### Q1: 为什么板块涨幅显示0.05%而不是5%？
**A:** 东方财富的f3字段已经是百分比数值，不需要再除以100。

### Q2: 如何获取实时数据？
**A:** 东方财富接口在交易时段返回实时数据，收盘后可能返回缓存数据。

### Q3: 新浪接口返回乱码？
**A:** 新浪使用GB2312编码，需要设置 `r.encoding = 'gb2312'`。

### Q4: 飞书token过期？
**A:** Token有效期约2小时，需要定期重新获取。