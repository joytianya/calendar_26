#!/usr/bin/env python3
"""
测试完成周期API的修复
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_complete_cycle_with_remark():
    """测试带有remark参数的完成周期API"""
    print("=== 测试完成周期API修复 ===")
    
    try:
        # 1. 获取当前周期
        print("1. 获取当前周期...")
        response = requests.get(f"{BASE_URL}/cycles")
        if response.status_code != 200:
            print(f"❌ 获取周期失败: {response.status_code}")
            return False
            
        cycles = response.json()
        current_cycle = None
        for cycle in cycles:
            if not cycle.get('is_completed', True):
                current_cycle = cycle
                break
                
        if not current_cycle:
            print("❌ 没有找到活跃的周期")
            return False
            
        print(f"✅ 找到当前周期: ID={current_cycle['id']}")
        
        # 2. 测试不带remark的完成周期（应该失败）
        print("2. 测试不带remark的完成周期...")
        response = requests.post(f"{BASE_URL}/cycles/{current_cycle['id']}/complete")
        if response.status_code == 400:
            print("✅ 正确返回400错误（remark必填）")
        else:
            print(f"❌ 期望400错误，但得到: {response.status_code}")
            
        # 3. 测试带有remark的完成周期（应该成功）
        print("3. 测试带有remark的完成周期...")
        test_remark = "测试完成周期"
        response = requests.post(
            f"{BASE_URL}/cycles/{current_cycle['id']}/complete",
            params={"remark": test_remark}
        )
        
        if response.status_code == 200:
            print("✅ 成功完成周期")
            completed_cycle = response.json()
            print(f"   - 周期ID: {completed_cycle['id']}")
            print(f"   - 结束时间: {completed_cycle['end_date']}")
            print(f"   - 备注: {completed_cycle['remark']}")
            print(f"   - 是否完成: {completed_cycle['is_completed']}")
            return True
        else:
            print(f"❌ 完成周期失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        return False

def test_frontend_api_format():
    """测试前端API格式的调用"""
    print("\n=== 测试前端API格式 ===")
    
    try:
        # 获取当前周期
        response = requests.get(f"{BASE_URL}/cycles")
        if response.status_code != 200:
            print(f"❌ 获取周期失败: {response.status_code}")
            return False
            
        cycles = response.json()
        current_cycle = None
        for cycle in cycles:
            if not cycle.get('is_completed', True):
                current_cycle = cycle
                break
                
        if not current_cycle:
            print("ℹ️ 没有活跃周期，创建一个新周期进行测试")
            # 创建新周期
            response = requests.post(f"{BASE_URL}/cycles", json={})
            if response.status_code == 200:
                current_cycle = response.json()
                print(f"✅ 创建新周期: ID={current_cycle['id']}")
            else:
                print(f"❌ 创建周期失败: {response.status_code}")
                return False
        
        # 测试前端格式的API调用（使用params传递remark）
        print("测试前端格式的API调用...")
        test_remark = "周期自然完成（达到26天）"
        
        # 模拟前端的调用方式
        response = requests.post(
            f"{BASE_URL}/cycles/{current_cycle['id']}/complete",
            params={"remark": test_remark}
        )
        
        if response.status_code == 200:
            print("✅ 前端格式API调用成功")
            completed_cycle = response.json()
            print(f"   - 备注: {completed_cycle['remark']}")
            return True
        else:
            print(f"❌ 前端格式API调用失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试完成周期API修复...")
    
    success1 = test_complete_cycle_with_remark()
    success2 = test_frontend_api_format()
    
    print(f"\n=== 测试结果 ===")
    print(f"基本API测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"前端格式测试: {'✅ 通过' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        print("🎉 所有测试通过！API修复成功。")
    else:
        print("⚠️ 部分测试失败，需要进一步检查。") 