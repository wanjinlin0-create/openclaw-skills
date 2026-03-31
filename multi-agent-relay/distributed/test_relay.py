#!/usr/bin/env python3
"""
测试脚本 - 验证分布式架构是否正常工作
"""

import requests
import json
import sys

COORDINATOR_URL = "http://localhost:9000"


def test_health():
    """测试协调器健康状态"""
    print("\n[测试1] 检查协调器健康状态...")
    try:
        response = requests.get(f"{COORDINATOR_URL}/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ 协调器在线")
            return True
        else:
            print(f"  ❌ 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False


def test_nodes():
    """测试节点状态"""
    print("\n[测试2] 检查节点状态...")
    try:
        response = requests.get(f"{COORDINATOR_URL}/nodes", timeout=5)
        if response.status_code == 200:
            nodes = response.json()
            online_count = sum(1 for n in nodes.values() if n.get("online"))
            total_count = len(nodes)
            print(f"  节点状态: {online_count}/{total_count} 在线")
            for role, info in nodes.items():
                icon = "🟢" if info.get("online") else "🔴"
                print(f"    {icon} {role}: {info.get('url', 'N/A')}")
            return online_count > 0
        else:
            print(f"  ❌ 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return False


def test_relay():
    """测试接力任务"""
    print("\n[测试3] 执行接力任务...")
    print("  ⚠️  此测试需要至少一个节点在线")
    
    task = {
        "content": "这是一个测试任务：请介绍一下分布式系统的基本概念。",
        "task_id": "test_task_001"
    }
    
    try:
        print("  发送任务到协调器...")
        response = requests.post(
            f"{COORDINATOR_URL}/relay",
            json=task,
            timeout=1200  # 20分钟超时（4个节点各5分钟）
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n  ✅ 任务完成!")
            print(f"     任务ID: {result.get('task_id')}")
            print(f"     状态: {result.get('status')}")
            print(f"     完成阶段: {len(result.get('stages', []))}/4")
            
            # 显示各阶段输出摘要
            print("\n  各阶段输出摘要:")
            for stage in result.get('stages', []):
                role = stage.get('role', 'unknown')
                output = stage.get('output', '')
                print(f"    • {role}: {output[:100]}...")
            
            return result.get('status') == 'success'
        else:
            print(f"  ❌ 状态码: {response.status_code}")
            print(f"  响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("  🧪 分布式多智能体架构测试")
    print("="*60)
    print(f"  协调器地址: {COORDINATOR_URL}")
    print("="*60)
    
    # 运行测试
    results = []
    
    results.append(("健康检查", test_health()))
    results.append(("节点状态", test_nodes()))
    
    # 询问是否执行接力测试
    print("\n" + "-"*60)
    response = input("是否执行接力任务测试？(需要节点在线) [y/N]: ")
    if response.lower() == 'y':
        results.append(("接力任务", test_relay()))
    else:
        print("  跳过接力任务测试")
    
    # 显示结果
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")
    
    all_passed = all(passed for _, passed in results)
    print("="*60)
    if all_passed:
        print("  🎉 所有测试通过！架构工作正常。")
    else:
        print("  ⚠️  部分测试失败，请检查配置。")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
