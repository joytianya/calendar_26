#!/usr/bin/env python3
"""
强制更新数据库脚本
以新的编辑后的历史记录时间区间为准，重新计算所有周期的有效天数和小时数
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
from datetime import datetime
from app.database.database import get_db
from app.models import models
from app.services.calendar_service import calculate_valid_days_and_hours

def force_update_all_cycles():
    """强制更新所有周期的计算数据"""
    print("=== 强制更新数据库 ===")
    
    try:
        # 获取所有周期
        response = requests.get('http://localhost:8000/api/cycles/')
        if response.status_code != 200:
            print(f"❌ 获取周期数据失败: {response.status_code}")
            return
        
        cycles = response.json()
        print(f"📊 找到 {len(cycles)} 个周期")
        
        # 直接连接数据库进行更新
        db = next(get_db())
        
        for cycle_data in cycles:
            cycle_id = cycle_data['id']
            cycle_number = cycle_data['cycle_number']
            
            print(f"\n🔄 处理周期 {cycle_number} (ID: {cycle_id})")
            
            # 获取数据库中的周期记录
            cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == cycle_id).first()
            if not cycle:
                print(f"❌ 数据库中未找到周期 {cycle_id}")
                continue
            
            print(f"  当前开始时间: {cycle.start_date}")
            print(f"  当前结束时间: {cycle.end_date}")
            print(f"  当前有效天数: {cycle.valid_days_count}")
            print(f"  当前有效小时数: {cycle.valid_hours_count:.2f}")
            
            # 获取跳过时间段
            skip_periods = db.query(models.SkipPeriod).filter(models.SkipPeriod.cycle_id == cycle_id).all()
            print(f"  跳过时间段数量: {len(skip_periods)}")
            
            # 重新计算有效天数和小时数
            try:
                valid_days, valid_hours = calculate_valid_days_and_hours(cycle, skip_periods)
                
                print(f"  重新计算结果:")
                print(f"    新有效天数: {valid_days}")
                print(f"    新有效小时数: {valid_hours:.2f}")
                
                # 检查是否需要更新
                needs_update = (
                    cycle.valid_days_count != valid_days or 
                    abs(cycle.valid_hours_count - valid_hours) > 0.01
                )
                
                if needs_update:
                    print(f"  ⚠️ 数据不一致，需要更新")
                    
                    # 更新数据库
                    old_days = cycle.valid_days_count
                    old_hours = cycle.valid_hours_count
                    
                    cycle.valid_days_count = valid_days
                    cycle.valid_hours_count = valid_hours
                    
                    db.commit()
                    
                    print(f"  ✅ 已更新:")
                    print(f"    天数: {old_days} -> {valid_days}")
                    print(f"    小时数: {old_hours:.2f} -> {valid_hours:.2f}")
                else:
                    print(f"  ✅ 数据一致，无需更新")
                    
            except Exception as e:
                print(f"  ❌ 计算失败: {e}")
                import traceback
                traceback.print_exc()
        
        db.close()
        print(f"\n🎉 所有周期处理完成")
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()

def verify_updates():
    """验证更新结果"""
    print("\n=== 验证更新结果 ===")
    
    try:
        response = requests.get('http://localhost:8000/api/cycles/')
        cycles = response.json()
        
        for cycle in cycles:
            print(f"\n周期 {cycle['cycle_number']} (ID: {cycle['id']}):")
            print(f"  有效天数: {cycle['valid_days_count']}")
            print(f"  有效小时数: {cycle['valid_hours_count']:.2f}")
            
            # 检查周期2的特殊情况
            if cycle['cycle_number'] == 2:
                print(f"  📊 周期2详细信息:")
                print(f"    开始时间: {cycle['start_date']}")
                print(f"    结束时间: {cycle['end_date']}")
                
                # 计算实际时间差
                start_time = datetime.fromisoformat(cycle['start_date'].replace('Z', ''))
                end_time = datetime.fromisoformat(cycle['end_date'].replace('Z', ''))
                total_duration = end_time - start_time
                total_hours = total_duration.total_seconds() / 3600
                
                print(f"    总时长: {total_duration}")
                print(f"    总小时数: {total_hours:.2f}")
                
                # 获取跳过时间段
                skip_response = requests.get(f'http://localhost:8000/api/calendar/skip-periods/{cycle["id"]}')
                skip_periods = skip_response.json()
                
                total_skip_hours = 0
                for skip in skip_periods:
                    skip_start = datetime.fromisoformat(skip['start_time'].replace('Z', ''))
                    skip_end = datetime.fromisoformat(skip['end_time'].replace('Z', ''))
                    skip_duration = skip_end - skip_start
                    skip_hours = skip_duration.total_seconds() / 3600
                    total_skip_hours += skip_hours
                
                expected_hours = total_hours - total_skip_hours
                expected_days = min(26, int(expected_hours / 24))
                
                print(f"    跳过小时数: {total_skip_hours:.2f}")
                print(f"    期望有效小时数: {expected_hours:.2f}")
                print(f"    期望有效天数: {expected_days}")
                
                hours_match = abs(cycle['valid_hours_count'] - expected_hours) < 0.1
                days_match = cycle['valid_days_count'] == expected_days
                
                print(f"    小时数正确: {'✅' if hours_match else '❌'}")
                print(f"    天数正确: {'✅' if days_match else '❌'}")
                
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    print("开始强制更新数据库...")
    force_update_all_cycles()
    verify_updates()
    print("\n✅ 更新完成!") 