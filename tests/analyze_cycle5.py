#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# 获取周期数据
response = requests.get("http://localhost:8000/api/cycles/")
data = response.json()

for cycle in data:
    if cycle['cycle_number'] == 5:
        print('周期5详细信息:')
        print(f'开始时间: {cycle["start_date"]}')
        print(f'结束时间: {cycle["end_date"]}')
        print(f'有效天数: {cycle["valid_days_count"]}')
        print(f'有效小时数: {cycle["valid_hours_count"]:.2f}')
        print(f'是否完成: {cycle.get("is_completed", False)}')
        print()
        
        # 计算时间差
        start = datetime.fromisoformat(cycle['start_date'])
        if cycle['end_date']:
            end = datetime.fromisoformat(cycle['end_date'])
        else:
            end = datetime.now()
            print(f'使用当前时间作为结束时间: {end}')
        
        total_hours = (end - start).total_seconds() / 3600
        print(f'总时间差: {total_hours:.2f} 小时 ({total_hours/24:.2f} 天)')
        
        # 计算跳过时间
        total_skip = 0
        skip_periods = cycle.get('skip_period_records', [])
        print(f'跳过时间段数量: {len(skip_periods)}')
        
        for skip in skip_periods:
            print(f'  日期: {skip["date"]}, 时间: {skip["start_time"]} - {skip["end_time"]}')
            start_h, start_m = map(int, skip['start_time'].split(':'))
            end_h, end_m = map(int, skip['end_time'].split(':'))
            skip_hours = (end_h - start_h) + (end_m - start_m) / 60
            total_skip += skip_hours
            print(f'    跳过: {skip_hours:.2f} 小时')
        
        print(f'总跳过时间: {total_skip:.2f} 小时')
        expected_valid = total_hours - total_skip
        print(f'预期有效时间: {expected_valid:.2f} 小时')
        print(f'实际有效时间: {cycle["valid_hours_count"]:.2f} 小时')
        print(f'差异: {abs(expected_valid - cycle["valid_hours_count"]):.2f} 小时')
        
        print('\n=== 问题分析 ===')
        if total_hours > 0 and cycle["valid_hours_count"] == 0:
            print('❌ 问题: 存在时间差但有效小时数为0')
            print(f'   应该有 {expected_valid:.2f} 小时的有效时间')
        
        if cycle["valid_days_count"] == 0 and expected_valid > 0:
            print('❌ 问题: 有效天数为0但应该有有效时间')
            print(f'   预期有效天数: {int(expected_valid / 24)}')
        
        # 检查是否是计算逻辑问题
        if expected_valid > 0 and cycle["valid_hours_count"] == 0:
            print('\n可能的原因:')
            print('1. 计算函数中的时间范围检查有问题')
            print('2. 周期开始时间晚于结束时间（逻辑错误）')
            print('3. 跳过时间段覆盖了整个周期时间')
            print('4. 数据库更新失败')
        
        break 