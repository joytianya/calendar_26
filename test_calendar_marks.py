#!/usr/bin/env python3
"""
测试日历标记功能
验证开始日期、结束日期、跳过日期、有效日期等标记是否正常显示
"""

import sys
import os
import requests
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API基础URL
API_BASE_URL = "http://101.126.143.26:8000"

def test_api_connection():
    """测试API连接"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health-check", timeout=10)
        if response.status_code == 200:
            print("✅ API连接正常")
            return True
        else:
            print(f"❌ API连接失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API连接异常: {e}")
        return False

def get_current_cycle():
    """获取当前周期"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/cycles/current")
        if response.status_code == 200:
            cycle = response.json()
            print(f"✅ 获取当前周期成功: 周期#{cycle['cycle_number']}")
            print(f"   开始时间: {cycle['start_date']}")
            print(f"   结束时间: {cycle.get('end_date', '进行中')}")
            print(f"   有效天数: {cycle['valid_days_count']}")
            print(f"   有效小时数: {cycle['valid_hours_count']}")
            return cycle
        else:
            print(f"❌ 获取当前周期失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 获取当前周期异常: {e}")
        return None

def get_calendar_data(start_date, end_date):
    """获取日历数据"""
    try:
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = requests.get(f"{API_BASE_URL}/api/calendar/data", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取日历数据成功，包含 {len(data['days'])} 天的数据")
            return data
        else:
            print(f"❌ 获取日历数据失败，状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 获取日历数据异常: {e}")
        return None

def analyze_calendar_marks(calendar_data, current_cycle):
    """分析日历标记"""
    if not calendar_data or not current_cycle:
        print("❌ 缺少必要数据，无法分析标记")
        return
    
    print("\n📅 日历标记分析:")
    print("=" * 50)
    
    # 解析周期开始和结束日期
    cycle_start_date = datetime.fromisoformat(current_cycle['start_date'].replace('Z', '+00:00')).date()
    cycle_end_date = None
    if current_cycle.get('end_date'):
        cycle_end_date = datetime.fromisoformat(current_cycle['end_date'].replace('Z', '+00:00')).date()
    
    print(f"周期开始日期: {cycle_start_date}")
    print(f"周期结束日期: {cycle_end_date or '进行中'}")
    
    # 统计各种标记
    start_days = []
    end_days = []
    skipped_days = []
    valid_days = []
    today = datetime.now().date()
    
    for day in calendar_data['days']:
        day_date = datetime.fromisoformat(day['date'].replace('Z', '+00:00')).date()
        
        # 检查是否是开始日
        if day_date == cycle_start_date:
            start_days.append(day_date)
        
        # 检查是否是结束日
        if cycle_end_date and day_date == cycle_end_date:
            end_days.append(day_date)
        
        # 检查是否是跳过日
        if day['is_skipped']:
            skipped_days.append({
                'date': day_date,
                'skip_period': day.get('skip_period')
            })
        
        # 检查是否是有效日
        if day.get('is_valid', False):
            valid_days.append(day_date)
    
    print(f"\n🟢 开始日标记: {len(start_days)} 个")
    for date in start_days:
        print(f"   - {date}")
    
    print(f"\n🔴 结束日标记: {len(end_days)} 个")
    for date in end_days:
        print(f"   - {date}")
    
    print(f"\n🟠 跳过日标记: {len(skipped_days)} 个")
    for skip_info in skipped_days:
        skip_period = skip_info['skip_period']
        if skip_period:
            print(f"   - {skip_info['date']} ({skip_period['start_time']} - {skip_period['end_time']})")
        else:
            print(f"   - {skip_info['date']} (无跳过时间段信息)")
    
    print(f"\n✅ 有效日标记: {len(valid_days)} 个")
    for date in valid_days[:5]:  # 只显示前5个
        print(f"   - {date}")
    if len(valid_days) > 5:
        print(f"   ... 还有 {len(valid_days) - 5} 个有效日")
    
    print(f"\n🔵 今天标记: {today}")
    
    # 验证标记逻辑
    print(f"\n🔍 标记验证:")
    print("=" * 30)
    
    # 验证开始日标记
    if len(start_days) == 1:
        print("✅ 开始日标记正确")
    else:
        print(f"❌ 开始日标记异常，应该有1个，实际有{len(start_days)}个")
    
    # 验证结束日标记
    if cycle_end_date:
        if len(end_days) == 1:
            print("✅ 结束日标记正确")
        else:
            print(f"❌ 结束日标记异常，应该有1个，实际有{len(end_days)}个")
    else:
        print("ℹ️  周期未结束，无结束日标记")
    
    # 验证有效日标记
    expected_valid_days = current_cycle['valid_days_count']
    if len(valid_days) >= expected_valid_days:
        print(f"✅ 有效日标记基本正确 (标记:{len(valid_days)}, 预期:≥{expected_valid_days})")
    else:
        print(f"❌ 有效日标记可能不足 (标记:{len(valid_days)}, 预期:≥{expected_valid_days})")

def main():
    """主函数"""
    print("🧪 开始测试日历标记功能")
    print("=" * 50)
    
    # 1. 测试API连接
    if not test_api_connection():
        return
    
    # 2. 获取当前周期
    current_cycle = get_current_cycle()
    if not current_cycle:
        return
    
    # 3. 获取日历数据
    # 计算日期范围：从周期开始日期前后各扩展一些天数
    cycle_start = datetime.fromisoformat(current_cycle['start_date'].replace('Z', '+00:00'))
    start_date = (cycle_start - timedelta(days=5)).isoformat()
    end_date = (cycle_start + timedelta(days=35)).isoformat()
    
    calendar_data = get_calendar_data(start_date, end_date)
    if not calendar_data:
        return
    
    # 4. 分析日历标记
    analyze_calendar_marks(calendar_data, current_cycle)
    
    print(f"\n✅ 日历标记功能测试完成")
    print("请检查前端页面，确认以下标记是否正确显示：")
    print("- 🟢 开始日：绿色背景 + '开始'标签")
    print("- 🔴 结束日：红色背景 + '结束'标签")
    print("- 🟠 跳过日：橙色背景 + '跳过'标签")
    print("- ✅ 有效日：浅绿色背景 + ✓ 标记")
    print("- 🔵 今天：蓝色边框 + '今天'标签")

if __name__ == "__main__":
    main() 