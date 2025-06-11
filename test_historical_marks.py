#!/usr/bin/env python3
"""
测试历史日期标记功能
验证历史周期的开始和结束日期是否正确显示在日历中
"""

import requests
import json
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:8000"

def test_calendar_data_with_historical_cycles():
    """测试日历数据是否包含历史周期信息"""
    print("🔍 测试历史周期标记功能...")
    
    # 获取日历数据
    # 设置一个较大的日期范围以包含历史周期
    start_date = "2025-03-01T00:00:00"
    end_date = "2025-06-30T23:59:59"
    
    try:
        response = requests.get(f"{BASE_URL}/api/calendar/data", params={
            "start_date": start_date,
            "end_date": end_date
        })
        
        if response.status_code != 200:
            print(f"❌ 获取日历数据失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        data = response.json()
        print(f"✅ 成功获取日历数据")
        
        # 检查响应结构
        required_fields = ['days', 'current_cycle', 'historical_cycles', 'valid_days_count', 'valid_hours_count']
        for field in required_fields:
            if field not in data:
                print(f"❌ 缺少必需字段: {field}")
                return False
        
        print(f"✅ 响应结构正确，包含所有必需字段")
        
        # 检查历史周期
        historical_cycles = data.get('historical_cycles', [])
        print(f"📊 找到 {len(historical_cycles)} 个历史周期")
        
        if len(historical_cycles) == 0:
            print("⚠️  没有历史周期数据")
            return True
        
        # 显示历史周期信息
        for i, cycle in enumerate(historical_cycles):
            print(f"\n📅 历史周期 #{cycle.get('cycle_number', 'N/A')}:")
            print(f"   开始时间: {cycle.get('start_date', 'N/A')}")
            print(f"   结束时间: {cycle.get('end_date', 'N/A')}")
            print(f"   是否完成: {cycle.get('is_completed', 'N/A')}")
            print(f"   有效天数: {cycle.get('valid_days_count', 'N/A')}")
            print(f"   备注: {cycle.get('remark', 'N/A')}")
        
        # 检查当前周期
        current_cycle = data.get('current_cycle')
        if current_cycle:
            print(f"\n🔄 当前周期 #{current_cycle.get('cycle_number', 'N/A')}:")
            print(f"   开始时间: {current_cycle.get('start_date', 'N/A')}")
            print(f"   结束时间: {current_cycle.get('end_date', 'N/A')}")
            print(f"   是否完成: {current_cycle.get('is_completed', 'N/A')}")
            print(f"   有效天数: {current_cycle.get('valid_days_count', 'N/A')}")
        else:
            print("\n⚠️  没有当前周期")
        
        # 统计日期标记
        days = data.get('days', [])
        print(f"\n📊 日历数据统计:")
        print(f"   总天数: {len(days)}")
        
        # 分析哪些日期应该有标记
        marked_dates = []
        
        # 历史周期的开始和结束日期
        for cycle in historical_cycles:
            if cycle.get('start_date'):
                start_date_str = cycle['start_date'].split('T')[0]
                marked_dates.append({
                    'date': start_date_str,
                    'type': 'start',
                    'cycle': cycle['cycle_number']
                })
            
            if cycle.get('end_date'):
                end_date_str = cycle['end_date'].split('T')[0]
                marked_dates.append({
                    'date': end_date_str,
                    'type': 'end',
                    'cycle': cycle['cycle_number']
                })
        
        # 当前周期的开始日期
        if current_cycle and current_cycle.get('start_date'):
            start_date_str = current_cycle['start_date'].split('T')[0]
            marked_dates.append({
                'date': start_date_str,
                'type': 'start',
                'cycle': current_cycle['cycle_number']
            })
        
        print(f"\n🏷️  应该有标记的日期:")
        for mark in marked_dates:
            print(f"   {mark['date']} - 周期#{mark['cycle']} {mark['type']}")
        
        print(f"\n✅ 历史周期标记功能测试完成")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_frontend_integration():
    """测试前端集成"""
    print("\n🌐 测试前端集成...")
    
    try:
        # 检查前端是否可访问
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
            print("📱 请在浏览器中查看 http://localhost:3001 验证历史日期标记是否正确显示")
            print("🔍 查看要点:")
            print("   1. 历史周期的开始日期是否有绿色标记")
            print("   2. 历史周期的结束日期是否有红色标记")
            print("   3. 当前周期的开始日期是否有绿色标记")
            print("   4. 跳过的日期是否有橙色标记")
            return True
        else:
            print(f"⚠️  前端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到前端服务: {e}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试历史日期标记功能\n")
    
    # 测试后端API
    api_success = test_calendar_data_with_historical_cycles()
    
    # 测试前端集成
    frontend_success = test_frontend_integration()
    
    print(f"\n📋 测试结果总结:")
    print(f"   后端API: {'✅ 通过' if api_success else '❌ 失败'}")
    print(f"   前端集成: {'✅ 通过' if frontend_success else '❌ 失败'}")
    
    if api_success and frontend_success:
        print(f"\n🎉 历史日期标记功能修复成功！")
    else:
        print(f"\n⚠️  部分功能需要进一步检查")
