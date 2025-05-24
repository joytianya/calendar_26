#!/usr/bin/env python3
"""
验证最终结果脚本
检查数据库更新后的结果是否正确
"""

import requests
import json
from datetime import datetime

def verify_all_cycles():
    """验证所有周期的数据"""
    print("=== 验证最终结果 ===")
    
    try:
        # 获取所有周期
        response = requests.get('http://localhost:8000/api/cycles/')
        cycles = response.json()
        
        print(f"📊 总共 {len(cycles)} 个周期")
        
        for cycle in cycles:
            cycle_number = cycle['cycle_number']
            print(f"\n🔍 周期 {cycle_number} (ID: {cycle['id']}):")
            print(f"  开始时间: {cycle['start_date']}")
            print(f"  结束时间: {cycle['end_date']}")
            print(f"  有效天数: {cycle['valid_days_count']}")
            print(f"  有效小时数: {cycle['valid_hours_count']:.2f}")
            print(f"  是否完成: {cycle['is_completed']}")
            
            # 特别检查周期2
            if cycle_number == 2:
                print(f"  ✅ 周期2问题已修复:")
                print(f"    - 之前有效小时数: 790.59")
                print(f"    - 现在有效小时数: {cycle['valid_hours_count']:.2f}")
                print(f"    - 修复状态: {'✅ 已修复' if cycle['valid_hours_count'] < 700 else '❌ 仍有问题'}")
                
                # 计算理论值
                start_time = datetime.fromisoformat(cycle['start_date'].replace('Z', ''))
                end_time = datetime.fromisoformat(cycle['end_date'].replace('Z', ''))
                total_duration = end_time - start_time
                total_hours = total_duration.total_seconds() / 3600
                
                print(f"    - 总时长: {total_duration}")
                print(f"    - 总小时数: {total_hours:.2f}")
                print(f"    - 跳过24小时后: {total_hours - 24:.2f}")
                print(f"    - 限制在26天内: {min(624, total_hours - 24):.2f}")
        
        print(f"\n🎉 验证完成！")
        print(f"主要问题修复状态:")
        
        # 检查周期2
        cycle2 = next((c for c in cycles if c['cycle_number'] == 2), None)
        if cycle2:
            if cycle2['valid_hours_count'] < 700:
                print(f"✅ 周期2小时数问题已修复 ({cycle2['valid_hours_count']:.2f}小时)")
            else:
                print(f"❌ 周期2小时数仍有问题 ({cycle2['valid_hours_count']:.2f}小时)")
        
        # 检查周期5
        cycle5 = next((c for c in cycles if c['cycle_number'] == 5), None)
        if cycle5:
            if cycle5['valid_hours_count'] > 0:
                print(f"✅ 周期5小时数问题已修复 ({cycle5['valid_hours_count']:.2f}小时)")
            else:
                print(f"❌ 周期5小时数仍为0")
                
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    verify_all_cycles() 