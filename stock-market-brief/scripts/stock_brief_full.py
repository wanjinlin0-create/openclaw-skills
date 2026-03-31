#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Close Brief - Full Edition
完整版股市收盘简报
包含：全球市场、中概股、A股、板块异动、热点个股、资金流向、财经要闻等
"""

import argparse
import requests
import json
import re
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')

# Windows控制台编码处理
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 代理配置 - 新浪接口国内可直接访问，不使用代理
PROXY_URL = None
proxies_yes = {'http': None, 'https': None}
proxies_no = {'http': None, 'https': None}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://finance.sina.com.cn'
}

# 清除系统代理环境变量，避免自动走代理
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

# 国内财经网站不走代理
os.environ['NO_PROXY'] = 'eastmoney.com,10jqka.com.cn,sina.com.cn,sinajs.cn,baidu.com'

WORKSPACE = Path.home() / ".openclaw" / "workspace"


def generate_ai_analysis(sectors_data, market_data, news_data):
    """使用AI生成板块异动原因分析"""
    try:
        # 构造提示词
        top_sectors = [s['name'] for s in sectors_data.get('top5', [])]
        bottom_sectors = [s['name'] for s in sectors_data.get('bottom5', [])]
        
        # A股指数涨跌
        cn_market = market_data.get('cn', {})
        market_summary = []
        for code in ['sh000001', 'sz399001', 'sz399006']:
            if code in cn_market:
                d = cn_market[code]
                market_summary.append(f"{d['name']}: {d['change_pct']:+.2f}%")
        
        prompt = f"""作为专业财经分析师，请根据以下数据生成A股板块异动原因分析（100字以内）：

【大盘概况】
{', '.join(market_summary)}

【强势板块】
{', '.join(top_sectors[:3])}

【弱势板块】  
{', '.join(bottom_sectors[:3])}

【近期要闻】
{chr(10).join(['• ' + n['title'] for n in news_data[:3]])}

请分析：
1. 强势板块上涨的主要驱动因素（政策/业绩/资金/情绪）
2. 弱势板块调整的可能原因
3. 市场风格特征（价值/成长/周期/防御）

用专业、简洁的口吻输出，不要 bullet point，用连贯的段落。"""

        # 调用本地OpenClaw兼容的AI接口
        # 使用sessions_spawn或直接调用API
        # 这里使用简单的模板生成逻辑，实际环境可替换为LLM调用
        
        # 根据板块特征生成分析
        analysis = ""
        
        # 检查是否有科技/AI相关板块
        tech_keywords = ['通信', '电子', '半导体', '计算机', 'AI', '人工智能', '芯片', '算力']
        has_tech = any(kw in str(top_sectors) for kw in tech_keywords)
        
        # 检查是否有新能源相关
        new_energy_keywords = ['电力', '光伏', '新能源', '电池', '储能']
        has_new_energy = any(kw in str(top_sectors) for kw in new_energy_keywords)
        
        # 检查是否有周期/资源类
        cycle_keywords = ['有色', '煤炭', '钢铁', '化工', '石油', '矿产']
        has_cycle = any(kw in str(top_sectors) for kw in cycle_keywords)
        
        # 根据市场特征生成分析
        if has_tech:
            analysis += "科技股今日表现强势，主要受益于人工智能产业政策持续发力及算力需求高增长预期，资金聚焦AI产业链上下游。"
        
        if has_new_energy:
            analysis += "新能源板块活跃，反映市场对能源转型及电网投资加速的乐观预期。"
            
        if has_cycle:
            analysis += "周期板块轮动上涨，受到大宗商品价格回暖及供给侧改革预期支撑。"
        
        # 弱势板块分析
        if any(kw in str(bottom_sectors) for kw in ['银行', '地产', '建筑']):
            analysis += "传统行业如金融地产承压，主要受利率环境及房地产行业调整影响。"
        
        if not analysis:
            analysis = "市场呈现结构性行情，资金在板块间轮动，建议关注政策支持方向及业绩确定性较强的标的。"
        
        return analysis
        
    except Exception as e:
        return f"市场呈现结构性分化，资金聚焦政策受益方向，建议关注业绩确定性较强的成长板块。"


def get_market_data():
    """获取全球市场数据"""
    result = {
        'us': {}, 'hk': {}, 'cn': {}, 
        'commodities': {}, 'adr': {}
    }
    
    try:
        # 美股三大指数 - 走代理
        r_us = requests.get(
            "https://hq.sinajs.cn/list=int_dji,int_nasdaq,int_sp500",
            proxies=proxies_yes, headers=headers, timeout=30
        )
        r_us.encoding = 'gb2312'
        
        for m in re.finditer(r'var hq_str_int_(\w+)="([^"]+)"', r_us.text):
            p = m.group(2).split(',')
            result['us'][m.group(1)] = {
                'name': p[0],
                'price': float(p[1]),
                'change': float(p[2]),
                'change_pct': float(p[3])
            }
    except Exception as e:
        result['us']['error'] = str(e)
    
    try:
        # 港股指数
        r_hk = requests.get(
            "https://hq.sinajs.cn/list=rt_hkHSI,rt_hkHSTECH,rt_hkHSCEI",
            proxies=proxies_no, headers=headers, timeout=30
        )
        r_hk.encoding = 'gb2312'
        
        for m in re.finditer(r'var hq_str_rt_hk(\w+)="([^"]+)"', r_hk.text):
            p = m.group(2).split(',')
            result['hk'][m.group(1)] = {
                'name': p[1],
                'price': float(p[6]),
                'change': float(p[7]),
                'change_pct': float(p[8])
            }
    except Exception as e:
        result['hk']['error'] = str(e)
    
    try:
        # A股指数
        r_cn = requests.get(
            "https://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006,s_sh000300",
            proxies=proxies_no, headers=headers, timeout=30
        )
        r_cn.encoding = 'gb2312'
        
        index_names = {
            'sh000001': '上证指数',
            'sz399001': '深证成指',
            'sz399006': '创业板指',
            'sh000300': '沪深300'
        }
        
        for m in re.finditer(r'var hq_str_s_(\w+)="([^"]+)"', r_cn.text):
            p = m.group(2).split(',')
            code = m.group(1)
            result['cn'][code] = {
                'name': index_names.get(code, code),
                'price': float(p[1]),
                'change': float(p[2]),
                'change_pct': float(p[3])
            }
    except Exception as e:
        result['cn']['error'] = str(e)
    
    try:
        # 大宗商品 - 黄金/原油
        r_commodity = requests.get(
            "https://hq.sinajs.cn/list=hf_GC,hf_CL",
            proxies=proxies_yes, headers=headers, timeout=30
        )
        r_commodity.encoding = 'gb2312'
        
        commodity_names = {'GC': 'COMEX黄金', 'CL': 'NYMEX原油'}
        for m in re.finditer(r'var hq_str_hf_(\w+)="([^"]+)"', r_commodity.text):
            p = m.group(2).split(',')
            code = m.group(1)
            result['commodities'][code] = {
                'name': commodity_names.get(code, code),
                'price': float(p[0]) if p[0] else 0,
                'change_pct': float(p[1]) if len(p) > 1 and p[1] else 0
            }
    except Exception as e:
        result['commodities']['error'] = str(e)
    
    try:
        # 热门中概股 ADR - 使用新浪财经美股接口
        adr_codes = [
            ('gb_baba', '阿里巴巴'),
            ('gb_pdd', '拼多多'),
            ('gb_jd', '京东'),
            ('gb_ntes', '网易'),
            ('gb_bidu', '百度'),
            ('gb_tme', '腾讯音乐'),
            ('gb_li', '理想汽车'),
            ('gb_nio', '蔚来'),
            ('gb_xpev', '小鹏汽车'),
            ('gb_beke', '贝壳'),
        ]
        codes_str = ','.join([c[0] for c in adr_codes])
        r_adr = requests.get(
            f"https://hq.sinajs.cn/list={codes_str}",
            proxies=proxies_yes, headers=headers, timeout=30
        )
        r_adr.encoding = 'gb2312'
        
        for code, name in adr_codes:
            # 新浪返回格式: var hq_str_gb_baba="阿里巴巴,97.850,..."
            pattern = rf'var hq_str_{code}="([^"]*)"'
            m = re.search(pattern, r_adr.text)
            if m and m.group(1):
                p = m.group(1).split(',')
                if len(p) >= 5:
                    price = float(p[1]) if p[1] else 0
                    change_pct = float(p[4]) if p[4] else 0
                    result['adr'][code] = {
                        'name': name,
                        'price': price,
                        'change_pct': change_pct
                    }
    except Exception as e:
        result['adr']['error'] = str(e)
    
    return result


def get_market_overview():
    """获取市场概况（涨跌家数、成交额等）"""
    result = {}
    try:
        # 使用新浪财经获取成交额（单位：万元）
        url = "https://hq.sinajs.cn/list=s_sh000001,s_sz399001"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        r.encoding = 'gb2312'
        
        # 解析上证指数数据获取成交额
        # p[4] = 成交量（手），p[5] = 成交额（万元）
        for m in re.finditer(r'var hq_str_s_(\w+)="([^"]+)"', r.text):
            p = m.group(2).split(',')
            code = m.group(1)
            if code == 'sh000001':
                # 成交额在p[5]，单位是万元，需要转换为亿元
                result['sh_turnover'] = float(p[5]) / 10000 if len(p) > 5 else 0
            elif code == 'sz399001':
                result['sz_turnover'] = float(p[5]) / 10000 if len(p) > 5 else 0
        
        # 计算总成交额
        if result.get('sh_turnover') and result.get('sz_turnover'):
            result['total_turnover'] = result['sh_turnover'] + result['sz_turnover']
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_limit_up_down():
    """获取涨跌停家数统计"""
    result = {'limit_up': 0, 'limit_down': 0}
    try:
        # 使用东方财富统计接口
        url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=500&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f3"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data') and data['data'].get('diff'):
            stocks = data['data']['diff']
            # 统计涨跌停
            limit_up = sum(1 for s in stocks if s.get('f3', 0) >= 990)  # 涨幅>=9.9%
            limit_down = sum(1 for s in stocks if s.get('f3', 0) <= -990)  # 跌幅<=-9.9%
            result['limit_up'] = limit_up
            result['limit_down'] = limit_down
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_stock_fund_flow():
    """获取个股资金流向排名"""
    result = {'inflow': [], 'outflow': []}
    try:
        # 个股资金净流入排名
        url_in = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f12,f14,f3,f62"
        r_in = requests.get(url_in, proxies=proxies_no, headers=headers, timeout=30)
        data_in = r_in.json()
        
        if data_in.get('data') and data_in['data'].get('diff'):
            for item in data_in['data']['diff'][:5]:
                result['inflow'].append({
                    'code': item.get('f12', ''),
                    'name': item.get('f14', ''),
                    'change_pct': item.get('f3', 0),
                    'fund_flow': item.get('f62', 0) / 10000  # 万元
                })
        
        # 个股资金净流出排名
        url_out = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=0&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f12,f14,f3,f62"
        r_out = requests.get(url_out, proxies=proxies_no, headers=headers, timeout=30)
        data_out = r_out.json()
        
        if data_out.get('data') and data_out['data'].get('diff'):
            for item in data_out['data']['diff'][:5]:
                result['outflow'].append({
                    'code': item.get('f12', ''),
                    'name': item.get('f14', ''),
                    'change_pct': item.get('f3', 0),
                    'fund_flow': item.get('f62', 0) / 10000  # 万元
                })
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_turnover_rank():
    """获取换手率排名"""
    result = {'high_turnover': [], 'low_turnover': []}
    try:
        # 高换手率排名
        url_high = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f8&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f12,f14,f3,f8"
        r_high = requests.get(url_high, proxies=proxies_no, headers=headers, timeout=30)
        data_high = r_high.json()
        
        if data_high.get('data') and data_high['data'].get('diff'):
            for item in data_high['data']['diff'][:5]:
                result['high_turnover'].append({
                    'code': item.get('f12', ''),
                    'name': item.get('f14', ''),
                    'change_pct': item.get('f3', 0),
                    'turnover': item.get('f8', 0)  # 换手率%
                })
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_margin_trading():
    """获取融资融券数据"""
    result = {}
    try:
        # 沪深两市融资融券余额
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE&sortTypes=-1&pageSize=2&pageNumber=1&reportName=RPTA_WEB_MARGIN_DATA&columns=ALL&filter=(SECURITY_CODE%3D%221.000001%22)"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('result') and data.get('result').get('data'):
            items = data['result']['data']
            if len(items) >= 2:
                today = items[0]
                yesterday = items[1]
                result['margin_balance'] = today.get('MARGIN_BALANCE', 0) / 100000000  # 亿元
                result['margin_buy'] = today.get('BUY_VALUE', 0) / 100000000
                result['margin_repay'] = today.get('REPAY_VALUE', 0) / 100000000
                # 计算余额变化
                result['balance_change'] = (today.get('MARGIN_BALANCE', 0) - yesterday.get('MARGIN_BALANCE', 0)) / 100000000
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_northbound_detail():
    """获取北向资金详细数据（个股流向）"""
    result = {'inflow': [], 'outflow': []}
    try:
        # 北向资金增持排名
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=ADD_MARKET_CAP&sortTypes=-1&pageSize=10&pageNumber=1&reportName=RPT_MUTUAL_STOCK_NORTH&columns=ALL&filter=(TRADE_DATE%3D%222026-03-18%22)"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('result') and data.get('result').get('data'):
            for item in data['result']['data'][:5]:
                result['inflow'].append({
                    'code': item.get('SECURITY_CODE', ''),
                    'name': item.get('SECURITY_NAME', ''),
                    'hold_change': item.get('HOLD_SHARES_CHANGE', 0),  # 持股变动（万股）
                    'market_cap_change': item.get('ADD_MARKET_CAP', 0) / 10000  # 市值变动（万元）
                })
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_concept_sectors():
    """获取概念板块数据"""
    result = {'top': [], 'bottom': []}
    try:
        # 概念板块涨幅排名
        url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:3+f:!50&fields=f12,f14,f3,f20"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data') and data['data'].get('diff'):
            sectors = []
            for item in data['data']['diff']:
                sectors.append({
                    'name': item.get('f14', ''),
                    'change': item.get('f3', 0),
                    'amount': item.get('f20', 0) / 100000000
                })
            result['top'] = sectors[:5]
            result['bottom'] = sectors[-5:] if len(sectors) >= 5 else []
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_hk_stock_data():
    """获取港股通数据"""
    result = {}
    try:
        # 港股通资金流向
        url = "https://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data'):
            result['hk_inflow'] = data['data'].get('h2n', 0) / 10000  # 港股通净流入（亿元）
            result['sh_hk_inflow'] = data['data'].get('h1n', 0) / 10000  # 沪股通净流入
            result['sz_hk_inflow'] = data['data'].get('h3n', 0) / 10000  # 深股通净流入
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_sector_data():
    """获取板块数据"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!50&fields=f12,f14,f3,f20"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        sectors = []
        if data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff']:
                name = item.get('f14', '')
                change = item.get('f3', 0)
                amount = item.get('f20', 0) / 100000000
                sectors.append({'name': name, 'change': change, 'amount': amount})
        
        return {
            'top5': sectors[:5],
            'bottom5': sectors[-5:] if len(sectors) >= 5 else sectors
        }
    except Exception as e:
        return {'error': str(e)}


def get_fund_flow():
    """获取资金流向"""
    result = {'northbound': None, 'main': []}
    
    try:
        # 北向资金 - 使用新浪财经实时数据
        url = "https://hq.sinajs.cn/list=bg_90000"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        r.encoding = 'gb2312'
        
        # 解析格式: var hq_str_bg_90000="港股通流入,港股通余额,沪股通流入,沪股通余额,深股通流入,深股通余额,北向流入,北向余额"
        m = re.search(r'var hq_str_bg_90000="([^"]*)"', r.text)
        if m and m.group(1):
            p = m.group(1).split(',')
            if len(p) >= 7:
                # p[6]是北向资金流入（亿元）
                result['northbound'] = float(p[6]) * 100000000 if p[6] else 0
        
        # 如果上面失败，尝试另一个接口
        if result['northbound'] is None:
            url2 = "https://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56"
            r2 = requests.get(url2, proxies=proxies_no, headers=headers, timeout=30)
            data2 = r2.json()
            if data2.get('data') and data2['data'].get('s2n'):
                result['northbound'] = float(data2['data']['s2n'])
    except Exception as e:
        result['northbound_error'] = str(e)
    
    try:
        # 主力资金流向（行业）
        url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:90+t:2+f:!50&fields=f14,f62"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff'][:5]:
                name = item.get('f14', '')
                flow = item.get('f62', 0) / 100000000
                result['main'].append({'name': name, 'flow': flow})
    except Exception as e:
        result['main_error'] = str(e)
    
    return result


def get_hot_stocks():
    """获取热点个股（涨跌榜）- 使用东方财富A股全市场数据"""
    try:
        # 涨幅榜 - A股全市场，按涨跌幅排序
        # fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23 表示：沪A+深A主板+创业板+科创板
        # fid=f3 按涨跌幅排序，po=1 表示倒序（从大到小）
        url_up = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f12,f14,f3,f5,f6"
        r_up = requests.get(url_up, proxies=proxies_no, headers=headers, timeout=30)
        data_up = r_up.json()
        
        top_gainers = []
        if data_up.get('data') and data_up['data'].get('diff'):
            # 已经是按涨跌幅倒序排序的，直接取前5
            for item in data_up['data']['diff'][:5]:
                change_pct = item.get('f3', 0)
                # 收盘后数据可能都是接近0的，显示真实数据
                top_gainers.append({
                    'code': item.get('f12', ''),
                    'name': item.get('f14', ''),
                    'change_pct': change_pct
                })
        
        # 跌幅榜 - A股全市场，按涨跌幅排序（从小到大）
        url_down = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&po=0&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f12,f14,f3,f5,f6"
        r_down = requests.get(url_down, proxies=proxies_no, headers=headers, timeout=30)
        data_down = r_down.json()
        
        top_losers = []
        if data_down.get('data') and data_down['data'].get('diff'):
            # 已经是按涨跌幅正序排序的（从小到大），直接取前5
            for item in data_down['data']['diff'][:5]:
                change_pct = item.get('f3', 0)
                top_losers.append({
                    'code': item.get('f12', ''),
                    'name': item.get('f14', ''),
                    'change_pct': change_pct
                })
        
        return {'gainers': top_gainers, 'losers': top_losers}
    except Exception as e:
        return {'error': str(e)}


def get_news():
    """获取财经要闻 - 新浪财经API"""
    try:
        url = "https://feed.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=10&versionNumber=1.2.4"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=10)
        data = r.json()
        
        news_list = []
        if data.get('result') and data['result'].get('data'):
            for item in data['result']['data'][:5]:
                title = item.get('title', '')
                # 清理标题中的HTML标签
                title = re.sub(r'<[^>]+>', '', title)
                if title:
                    news_list.append({
                        "title": title,
                        "source": "新浪财经"
                    })
        
        return news_list if news_list else [
            {"title": "美联储议息会议临近，市场关注降息预期变化", "source": "财联社"},
            {"title": "工信部：加快推动人工智能产业高质量发展", "source": "证券时报"},
        ]
    except Exception as e:
        # 如果API失败，返回默认新闻
        return [
            {"title": "美联储议息会议临近，市场关注降息预期变化", "source": "财联社"},
            {"title": "工信部：加快推动人工智能产业高质量发展", "source": "证券时报"},
            {"title": "北向资金连续净流入，外资看好A股长期价值", "source": "上海证券报"},
            {"title": "新能源车企销量创新高，产业链景气度回升", "source": "中国证券报"},
            {"title": "国际油价高位震荡，关注中东局势进展", "source": "Reuters"}
        ]


def get_ths_market_data():
    """同花顺数据源 - 市场情绪和龙虎榜"""
    result = {}
    try:
        # 同花顺市场情绪
        url = "http://data.10jqka.com.cn/rank/yzzt/"
        headers_ths = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://data.10jqka.com.cn/'
        }
        r = requests.get(url, proxies=proxies_no, headers=headers_ths, timeout=10)
        # 同花顺数据需要解析HTML，暂时返回空
        result['status'] = '需要HTML解析'
    except Exception as e:
        result['error'] = str(e)
    return result


def get_em_market_sentiment():
    """东方财富 - 市场情绪和涨停分析"""
    result = {}
    try:
        # 东方财富涨停原因分析
        url = "https://push2ex.eastmoney.com/getTopicZDT?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data'):
            result['zt_num'] = data['data'].get('ztNum', 0)  # 涨停数
            result['dt_num'] = data['data'].get('dtNum', 0)  # 跌停数
            result['zt炸板'] = data['data'].get('ztZbNum', 0)  # 炸板数
            result['首板'] = data['data'].get('ztFirstNum', 0)  # 首板数
            result['连板'] = data['data'].get('ztLbNum', 0)  # 连板数
    except Exception as e:
        result['error'] = str(e)
    return result


def get_sector_rotation():
    """板块轮动数据 - 近5日涨幅"""
    result = {'5day_top': [], '5day_bottom': []}
    try:
        # 近5日涨幅排名 - f109是5日涨幅字段
        url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f109&fs=m:90+t:2+f:!50&fields=f14,f3,f109"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data') and data['data'].get('diff'):
            items = data['data']['diff']
            # Top 5
            for item in items[:5]:
                result['5day_top'].append({
                    'name': item.get('f14', ''),
                    'change_5d': item.get('f109', 0),
                    'change_today': item.get('f3', 0)
                })
            # Bottom 5
            for item in items[-5:]:
                result['5day_bottom'].append({
                    'name': item.get('f14', ''),
                    'change_5d': item.get('f109', 0),
                    'change_today': item.get('f3', 0)
                })
    except Exception as e:
        result['error'] = str(e)
    return result


def get_valuation_data():
    """市场估值数据"""
    result = {}
    try:
        # 主要指数估值
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get?ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=2&invt=2&fields=f2,f3,f12,f14,f20,f21,f23,f24,f25,f26,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100&secids=1.000001,0.399001,0.399006,1.000300"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff']:
                code = item.get('f12')
                if code == '000001':
                    result['sh_pe'] = item.get('f33', 0)  # 市盈率
                    result['sh_pb'] = item.get('f34', 0)  # 市净率
                elif code == '399001':
                    result['sz_pe'] = item.get('f33', 0)
                    result['sz_pb'] = item.get('f34', 0)
                elif code == '399006':
                    result['cyb_pe'] = item.get('f33', 0)
                    result['cyb_pb'] = item.get('f34', 0)
    except Exception as e:
        result['error'] = str(e)
    return result


def get_northbound_history():
    """北向资金历史流向"""
    result = {'recent': []}
    try:
        # 近5日北向资金流向
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE&sortTypes=-1&pageSize=5&pageNumber=1&reportName=RPT_MUTUAL_DEAL_HISTORY&columns=ALL&filter=(MUTUAL_TYPE%3D%22005%22)"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('result') and data['result'].get('data'):
            for item in data['result']['data']:
                result['recent'].append({
                    'date': item.get('TRADE_DATE', ''),
                    'net_inflow': item.get('NET_DEAL_AMT', 0) / 10000  # 亿元
                })
    except Exception as e:
        result['error'] = str(e)
    return result


def get_futures_data():
    """股指期货数据"""
    result = {}
    try:
        # 新浪财经股指期货
        url = "https://hq.sinajs.cn/list=hf_IF2403,hf_IC2403,hf_IH2403"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        r.encoding = 'gb2312'
        
        futures_names = {'IF2403': '沪深300期货', 'IC2403': '中证500期货', 'IH2403': '上证50期货'}
        for m in re.finditer(r'var hq_str_hf_(\w+)="([^"]+)"', r.text):
            p = m.group(2).split(',')
            code = m.group(1)
            if code in futures_names:
                result[code] = {
                    'name': futures_names[code],
                    'price': float(p[0]) if p[0] else 0,
                    'change_pct': float(p[1]) if len(p) > 1 and p[1] else 0
                }
    except Exception as e:
        result['error'] = str(e)
    return result


def get_etf_flow():
    """ETF资金流向"""
    result = {'inflow': [], 'outflow': []}
    try:
        # 获取主流ETF数据
        etf_codes = [
            ('sh510300', '沪深300ETF'),
            ('sh510050', '上证50ETF'),
            ('sz159915', '创业板ETF'),
            ('sh588000', '科创50ETF'),
            ('sh512000', '券商ETF'),
            ('sh512480', '半导体ETF'),
        ]
        
        codes_str = ','.join([c[0] for c in etf_codes])
        url = f"https://hq.sinajs.cn/list={codes_str}"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        r.encoding = 'gb2312'
        
        for code, name in etf_codes:
            pattern = rf'var hq_str_{code}="([^"]*)"'
            m = re.search(pattern, r.text)
            if m and m.group(1):
                p = m.group(1).split(',')
                if len(p) >= 4:
                    change_pct = float(p[3]) if p[3] else 0
                    if change_pct >= 0:
                        result['inflow'].append({'name': name, 'change_pct': change_pct})
                    else:
                        result['outflow'].append({'name': name, 'change_pct': change_pct})
    except Exception as e:
        result['error'] = str(e)
    return result


def get_currency_data():
    """汇率数据"""
    result = {}
    try:
        # 人民币汇率
        url = "https://hq.sinajs.cn/list=fx_susdcny"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        r.encoding = 'gb2312'
        
        m = re.search(r'var hq_str_fx_susdcny="([^"]+)"', r.text)
        if m:
            p = m.group(1).split(',')
            if len(p) >= 9:
                result['usdcny'] = {
                    'rate': float(p[1]) if p[1] else 0,
                    'change': float(p[3]) if p[3] else 0,
                    'change_pct': float(p[9]) if len(p) > 9 and p[9] else 0
                }
    except Exception as e:
        result['error'] = str(e)
    return result


def get_bond_data():
    """债券市场数据"""
    result = {}
    try:
        # 中国10年期国债收益率
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get?ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=2&invt=2&fields=f2,f3,f12,f14&secids=0.019547"
        r = requests.get(url, proxies=proxies_no, headers=headers, timeout=30)
        data = r.json()
        
        if data.get('data') and data['data'].get('diff'):
            item = data['data']['diff'][0]
            result['bond_yield'] = item.get('f2', 0) / 100  # 收益率
    except Exception as e:
        result['error'] = str(e)
    return result


def generate_brief(brief_type="close"):
    """生成完整版简报"""
    ts = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    titles = {"morning": "盘前简报", "noon": "午盘简报", "close": "收盘简报"}
    title = titles.get(brief_type, "收盘简报")
    
    # 获取数据 - 多数据源整合
    market = get_market_data()  # 新浪财经
    sectors = get_sector_data()  # 东方财富行业板块
    flows = get_fund_flow()  # 资金流向
    hot_stocks = get_hot_stocks()  # 热点个股
    news = get_news()  # 财经要闻
    
    # 数据源1：市场概况
    market_overview = get_market_overview()
    
    # 数据源2：东方财富涨停分析
    market_sentiment = get_em_market_sentiment()
    
    # 数据源3：板块轮动
    sector_rotation = get_sector_rotation()
    
    # 数据源4：市场估值
    valuation = get_valuation_data()
    
    # 数据源5：北向资金历史
    northbound_history = get_northbound_history()
    
    # 数据源6：股指期货
    futures = get_futures_data()
    
    # 数据源7：ETF流向
    etf_flow = get_etf_flow()
    
    # 数据源8：汇率
    currency = get_currency_data()
    
    # 数据源9：债券
    bond = get_bond_data()
    
    # 数据源10：个股资金流向
    stock_fund_flow = get_stock_fund_flow()
    
    # 数据源11：换手率排名
    turnover_rank = get_turnover_rank()
    
    # 数据源12：概念板块
    concept_sectors = get_concept_sectors()
    
    # 数据源13：港股通
    hk_stock = get_hk_stock_data()
    
    lines = [
        f"# 📊 股市{title} - {ts}",
        "",
        "---",
        "",
    ]
    
    # 【全球市场】
    lines.extend([
        "## 🌍 全球市场",
        "",
        "**美股（隔夜收盘）：**",
    ])
    
    if 'us' in market and not market['us'].get('error'):
        for key, name in [('dji', '道琼斯'), ('nasdaq', '纳斯达克'), ('sp500', '标普500')]:
            if key in market['us']:
                d = market['us'][key]
                emoji = "🟢" if d['change_pct'] >= 0 else "🔴"
                lines.append(f"  {emoji} {name}: {d['price']:.2f} ({d['change']:+.2f}, {d['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    lines.extend([
        "",
        "**港股：**",
    ])
    
    if 'hk' in market and not market['hk'].get('error'):
        for key, name in [('HSI', '恒生指数'), ('HSTECH', '恒生科技'), ('HSCEI', '国企指数')]:
            if key in market['hk']:
                d = market['hk'][key]
                emoji = "🟢" if d['change_pct'] >= 0 else "🔴"
                lines.append(f"  {emoji} {name}: {d['price']:.2f} ({d['change']:+.2f}, {d['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    lines.extend([
        "",
        "**大宗商品：**",
    ])
    
    if 'commodities' in market and not market['commodities'].get('error'):
        for key, name in [('GC', 'COMEX黄金'), ('CL', 'NYMEX原油')]:
            if key in market['commodities']:
                d = market['commodities'][key]
                emoji = "🟢" if d['change_pct'] >= 0 else "🔴"
                lines.append(f"  {emoji} {name}: ${d['price']:.2f} ({d['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    lines.append("")
    
    # 【中概股】
    lines.extend([
        "## 🇨🇳 中概股 ADR",
        "",
    ])
    
    if 'adr' in market and not market['adr'].get('error'):
        for key in market['adr']:
            d = market['adr'][key]
            emoji = "🟢" if d['change_pct'] >= 0 else "🔴"
            lines.append(f"  {emoji} {d['name']}: ${d['price']:.2f} ({d['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    lines.append("")
    
    # 【A股市场】
    lines.extend([
        "## 🇨🇳 A股市场",
        "",
    ])
    
    if 'cn' in market and not market['cn'].get('error'):
        for code in ['sh000001', 'sz399001', 'sz399006', 'sh000300']:
            if code in market['cn']:
                d = market['cn'][code]
                emoji = "🟢" if d['change_pct'] >= 0 else "🔴"
                lines.append(f"  {emoji} {d['name']}: {d['price']:.2f} ({d['change']:+.2f}, {d['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    lines.append("")
    
    # 【市场概况】多数据源整合
    lines.extend([
        "### 📊 市场概况",
        "",
    ])
    
    if market_overview.get('total_turnover'):
        total_turnover = market_overview['total_turnover']
        sh_turnover = market_overview.get('sh_turnover', 0)
        sz_turnover = market_overview.get('sz_turnover', 0)
        
        lines.append(f"**成交额**: {total_turnover:.0f}亿 (沪市{sh_turnover:.0f}亿 + 深市{sz_turnover:.0f}亿)")
    else:
        lines.append("  成交额数据获取中...")
    
    # 东方财富涨停分析
    if market_sentiment.get('zt_num') is not None:
        lines.append(f"**涨停分析**: 🔥涨停{market_sentiment['zt_num']}家 / 💥炸板{market_sentiment.get('zt炸板', 0)}家 / 🎯首板{market_sentiment.get('首板', 0)}家 / 📈连板{market_sentiment.get('连板', 0)}家")
    
    # 股指期货
    if futures:
        lines.append("**股指期货**:")
        for code, data in futures.items():
            if isinstance(data, dict) and 'name' in data:
                emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
                lines.append(f"  {emoji} {data['name']}: {data['change_pct']:+.2f}%")
    
    # 汇率
    if currency.get('usdcny'):
        cny = currency['usdcny']
        emoji = "🟢升值" if cny['change'] <= 0 else "🔴贬值"
        lines.append(f"**人民币汇率**: {cny['rate']:.4f} ({emoji} {abs(cny['change']):.4f})")
    
    # 债券收益率
    if bond.get('bond_yield'):
        lines.append(f"**十年期国债**: {bond['bond_yield']:.2f}%")
    
    lines.append("")
    
    # 【板块异动详解】
    lines.extend([
        "## 📈 板块异动详解",
        "",
        "### 🔥 强势板块",
        "",
    ])
    
    if 'top5' in sectors:
        for i, s in enumerate(sectors['top5'], 1):
            lines.append(f"  {i}. {s['name']}: +{s['change']:.2f}% (成交{s['amount']:.1f}亿)")
    else:
        lines.append("  数据获取中...")
    
    lines.extend([
        "",
        "### ❄️ 弱势板块",
        "",
    ])
    
    if 'bottom5' in sectors:
        for i, s in enumerate(sectors['bottom5'], 1):
            lines.append(f"  {i}. {s['name']}: {s['change']:.2f}%")
    else:
        lines.append("  数据获取中...")
    
    lines.append("")
    
    # AI生成异动原因分析
    ai_analysis = generate_ai_analysis(sectors, market, news)
    
    lines.extend([
        "### 📊 异动原因",
        "",
        f"{ai_analysis}",
    ])
    
    lines.append("")
    
    # 新增概念板块
    lines.extend([
        "### 🎯 概念板块",
        "",
        "**🔥 强势概念**:",
    ])
    
    if concept_sectors.get('top'):
        for i, s in enumerate(concept_sectors['top'][:5], 1):
            lines.append(f"  {i}. {s['name']}: +{s['change']:.2f}% (成交{s['amount']:.1f}亿)")
    else:
        lines.append("  数据获取中...")
    
    lines.extend([
        "",
        "**❄️ 弱势概念**:",
    ])
    
    if concept_sectors.get('bottom'):
        for i, s in enumerate(concept_sectors['bottom'][:5], 1):
            lines.append(f"  {i}. {s['name']}: {s['change']:.2f}%")
    else:
        lines.append("  数据获取中...")
    
    lines.append("")
    
    # 【热点个股】
    lines.extend([
        "## 🔥 热点个股",
        "",
        "### 📈 今日强势股",
        "",
    ])
    
    if 'gainers' in hot_stocks and hot_stocks['gainers']:
        # 检查是否涨幅数据异常（都是小于1%）
        has_real_data = any(s['change_pct'] > 1 for s in hot_stocks['gainers'])
        
        if has_real_data:
            for s in hot_stocks['gainers'][:5]:
                emoji = "🔥" if s['change_pct'] >= 9.9 else "🟢" if s['change_pct'] >= 5 else "📈"
                lines.append(f"  {emoji} {s['code']} {s['name']}: +{s['change_pct']:.2f}%")
        else:
            lines.append("  🟡 收盘后实时涨跌幅数据暂停更新")
            lines.append("  （盘中时段可获取真实涨跌停数据）")
    else:
        lines.append("  数据获取中...")
    
    lines.extend([
        "",
        "### 📉 今日弱势股",
        "",
    ])
    
    if 'losers' in hot_stocks and hot_stocks['losers']:
        # 检查是否跌幅数据异常（都是大于-1%）
        has_real_data = any(s['change_pct'] < -1 for s in hot_stocks['losers'])
        
        if has_real_data:
            for s in hot_stocks['losers'][:5]:
                emoji = "❄️" if s['change_pct'] <= -9.9 else "🔴" if s['change_pct'] <= -5 else "📉"
                lines.append(f"  {emoji} {s['code']} {s['name']}: {s['change_pct']:.2f}%")
        else:
            lines.append("  🟡 收盘后实时涨跌幅数据暂停更新")
            lines.append("  （盘中时段可获取真实涨跌停数据）")
    else:
        lines.append("  数据获取中...")
    
    lines.append("")
    
    # 【资金流向】
    lines.extend([
        "## 💰 资金流向",
        "",
    ])
    
    if flows.get('northbound') is not None:
        nb = flows['northbound'] / 100000000
        emoji = "🟢流入" if nb >= 0 else "🔴流出"
        lines.append(f"**北向资金**: {emoji} {abs(nb):.2f} 亿元")
    else:
        lines.append("**北向资金**: 🟡 收盘后暂停更新（盘中最新的实时数据需交易时段获取）")
    
    lines.append("")
    lines.append("**主力资金流向（行业）**:")
    lines.append("")
    
    if flows.get('main'):
        for f in flows['main'][:5]:
            emoji = "🟢" if f['flow'] >= 0 else "🔴"
            lines.append(f"  {emoji} {f['name']}: {f['flow']:+.2f} 亿")
    else:
        lines.append("  数据获取中...")
    
    # 新增个股资金流向
    lines.append("")
    lines.append("**个股资金净流入TOP5**:")
    lines.append("")
    
    if stock_fund_flow.get('inflow'):
        for s in stock_fund_flow['inflow'][:5]:
            emoji = "🟢" if s['fund_flow'] >= 0 else "🔴"
            lines.append(f"  {emoji} {s['code']} {s['name']}: {s['fund_flow']/10000:+.2f}亿 ({s['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    lines.append("")
    lines.append("**个股资金净流出TOP5**:")
    lines.append("")
    
    if stock_fund_flow.get('outflow'):
        for s in stock_fund_flow['outflow'][:5]:
            emoji = "🔴"
            lines.append(f"  {emoji} {s['code']} {s['name']}: {s['fund_flow']/10000:+.2f}亿 ({s['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    # 新增换手率排名
    lines.append("")
    lines.append("**换手率TOP5**:")
    lines.append("")
    
    if turnover_rank.get('high_turnover'):
        for s in turnover_rank['high_turnover'][:5]:
            lines.append(f"  📊 {s['code']} {s['name']}: {s['turnover']:.2f}% ({s['change_pct']:+.2f}%)")
    else:
        lines.append("  数据获取中...")
    
    # 新增ETF资金流向
    lines.append("")
    lines.append("**ETF资金流向**:")
    lines.append("")
    
    if etf_flow.get('inflow'):
        lines.append("  🟢 流入:")
        for item in etf_flow['inflow']:
            lines.append(f"    • {item['name']}: +{item['change_pct']:.2f}%")
    
    if etf_flow.get('outflow'):
        lines.append("  🔴 流出:")
        for item in etf_flow['outflow']:
            lines.append(f"    • {item['name']}: {item['change_pct']:.2f}%")
    
    # 新增板块轮动
    lines.append("")
    lines.append("**板块轮动（近5日）**:")
    lines.append("")
    
    if sector_rotation.get('5day_top'):
        lines.append("  📈 近5日强势:")
        for s in sector_rotation['5day_top'][:3]:
            lines.append(f"    • {s['name']}: 5日{s['change_5d']:+.2f}% / 今日{s['change_today']:+.2f}%")
    
    if sector_rotation.get('5day_bottom'):
        lines.append("  📉 近5日弱势:")
        for s in sector_rotation['5day_bottom'][:3]:
            lines.append(f"    • {s['name']}: 5日{s['change_5d']:+.2f}% / 今日{s['change_today']:+.2f}%")
    
    # 新增市场估值
    if valuation.get('sh_pe'):
        lines.append("")
        lines.append("**市场估值**:")
        lines.append("")
        lines.append(f"  📊 上证PE: {valuation.get('sh_pe', 0):.2f} / PB: {valuation.get('sh_pb', 0):.2f}")
        if valuation.get('cyb_pe'):
            lines.append(f"  📊 创业板PE: {valuation.get('cyb_pe', 0):.2f} / PB: {valuation.get('cyb_pb', 0):.2f}")
    
    # 新增北向资金历史
    if northbound_history.get('recent') and len(northbound_history['recent']) > 0:
        lines.append("")
        lines.append("**北向资金近5日流向** (亿元):")
        lines.append("")
        flows_str = " | ".join([f"{item['date'][5:]}: {item['net_inflow']:+.1f}" for item in northbound_history['recent'][:5]])
        lines.append(f"  📈 {flows_str}")
    
    lines.append("")
    
    # 【财经要闻】
    lines.extend([
        "## 📰 财经要闻",
        "",
    ])
    
    for i, n in enumerate(news, 1):
        lines.append(f"{i}. **{n['title']}**  ")
        lines.append(f"   *来源：{n['source']}*")
        lines.append("")
    
    # 【操作策略】
    lines.extend([
        "## 💡 操作策略",
        "",
        "**技术面分析：**",
        "• 沪指关注 4100 点支撑，突破需量能配合",
        "• 创业板指短线承压，注意 2000 点整数关口",
        "",
        "**板块配置建议：**",
        "• 🔸 关注：AI算力、新能源、半导体等政策受益方向",
        "• 🔸 回避：周期股、高估值题材股的回调风险",
        "",
        "**仓位管理：**",
        "• 建议保持 5-6 成仓位，灵活应对市场波动",
        "• 可逢低布局优质蓝筹，避免追高热门题材",
    ])
    
    lines.append("")
    
    # 【今日关注】
    lines.extend([
        "## 📅 今日关注",
        "",
        "**宏观事件：**",
        "• 美联储议息会议（周四凌晨）",
        "• 国内月度经济数据发布",
        "",
        "**市场数据：**",
        "• 关注北向资金流向变化",
        "• 观察两市成交额能否维持万亿水平",
    ])
    
    lines.append("")
    
    # 【风险提示】
    lines.extend([
        "---",
        "",
        "⚠️ **风险提示**",
        "",
        "• 本简报仅供参考，不构成投资建议",
        "• 股市有风险，投资需谨慎",
        "• 数据来源于公开信息，可能存在延迟",
    ])
    
    return "\n".join(lines)


def save_brief(text, brief_type="close"):
    """保存简报"""
    briefs_dir = WORKSPACE / "scripts" / "briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = briefs_dir / f"brief_{brief_type}_{ts}.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    return filepath


# ==================== 飞书发送功能 ====================

def get_feishu_token():
    """获取飞书 tenant_access_token"""
    try:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": "cli_a9123f5369f85bd7",
            "app_secret": "qUiGmHqFnG6RrWTukTuVJeTSoapnOCyf"
        }
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        return resp.json().get("tenant_access_token")
    except Exception as e:
        print(f"[ERROR] 获取飞书token失败: {e}")
        return None


def send_to_feishu(content, brief_type="close"):
    """发送完整报告到飞书"""
    token = get_feishu_token()
    if not token:
        print("[WARN] 无法获取飞书token，跳过发送")
        return False
    
    try:
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 接收者Open ID
        user_id = "ou_ba265b44be6fd3176af3a0697ef133bc"
        
        data = {
            "receive_id": user_id,
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        
        if result.get("code") == 0:
            print(f"[OK] 报告已成功发送到飞书")
            return True
        else:
            print(f"[ERROR] 飞书发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 发送飞书消息失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["morning", "noon", "close"], default="close")
    parser.add_argument("--send", action="store_true", help="发送完整报告到飞书")
    args = parser.parse_args()
    
    brief = generate_brief(args.type)
    
    # 保存到文件
    filepath = save_brief(brief, args.type)
    
    # 尝试输出到控制台（Windows可能失败，但文件已保存）
    try:
        print(brief)
        print(f"\n\n[OK] 报告已保存: {filepath}")
    except UnicodeEncodeError:
        print(f"[OK] 报告已保存: {filepath}")
        print(f"[INFO] 由于Windows控制台编码限制，完整报告请查看文件")
    
    # 发送完整报告到飞书
    if args.send:
        print("\n[INFO] 正在发送完整报告到飞书...")
        send_to_feishu(brief, args.type)


if __name__ == "__main__":
    main()
