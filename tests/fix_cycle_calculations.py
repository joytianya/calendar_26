#!/usr/bin/env python3
"""
修复所有周期的有效天数和小时数计算
"""

import requests
import json
from datetime import datetime

def fix_cycle_calculations():
    """修复所有周期的计算"""
    print("开始修复周期计算...")
    
    # 获取所有周期
    response = requests.get("http://localhost:8000/api/cycles/")
    if response.status_code != 200:
        print(f"获取周期失败: {response.status_code}")
        return
    
    cycles = response.json()
    print(f"找到 {len(cycles)} 个周期")
    
    for cycle in cycles:
        cycle_id = cycle['id']
        cycle_number = cycle['cycle_number']
        
        print(f"\n处理周期 #{cycle_number} (ID: {cycle_id})")
        print(f"  当前有效天数: {cycle['valid_days_count']}")
        print(f"  当前有效小时数: {cycle['valid_hours_count']:.2f}")
        
        # 计算正确的值
        start_date = datetime.fromisoformat(cycle['start_date'])
        end_date = datetime.fromisoformat(cycle['end_date']) if cycle['end_date'] else datetime.now()
        
        total_hours = (end_date - start_date).total_seconds() / 3600
        
        # 计算跳过时间
        total_skip_hours = 0
        skip_periods = cycle.get('skip_period_records', [])
        
        for skip in skip_periods:
            start_h, start_m = map(int, skip['start_time'].split(':'))
            end_h, end_m = map(int, skip['end_time'].split(':'))
            skip_hours = (end_h - start_h) + (end_m - start_m) / 60
            total_skip_hours += skip_hours
        
        correct_valid_hours = total_hours - total_skip_hours
        correct_valid_days = int(correct_valid_hours / 24)
        
        print(f"  正确有效天数: {correct_valid_days}")
        print(f"  正确有效小时数: {correct_valid_hours:.2f}")
        
        # 检查是否需要修复
        if (abs(cycle['valid_days_count'] - correct_valid_days) > 0 or 
            abs(cycle['valid_hours_count'] - correct_valid_hours) > 0.1):
            
            print(f"  需要修复！")
            
            # 通过编辑API触发重新计算
            update_data = {
                "start_date": cycle['start_date'],
                "remark": cycle.get('remark', '') + " [自动修复计算]"
            }
            
            if cycle['end_date']:
                update_data['end_date'] = cycle['end_date']
            
            response = requests.put(f"http://localhost:8000/api/cycles/{cycle_id}", json=update_data)
            
            if response.status_code == 200:
                updated_cycle = response.json()
                print(f"  修复成功！")
                print(f"    新有效天数: {updated_cycle['valid_days_count']}")
                print(f"    新有效小时数: {updated_cycle['valid_hours_count']:.2f}")
            else:
                print(f"  修复失败: {response.status_code} - {response.text}")
        else:
            print(f"  数据正确，无需修复")

if __name__ == "__main__":
    fix_cycle_calculations() 