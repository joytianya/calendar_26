#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# 获取周期数据
response = requests.get("http://localhost:8000/api/cycles/")
data = response.json()

for cycle in data:
    if cycle['cycle_number'] == 2:
        print('周期2详细信息:')
        print(f'开始时间: {cycle["start_date"]}')
        print(f'结束时间: {cycle["end_date"]}')
        print(f'有效天数: {cycle["valid_days_count"]}')
        print(f'有效小时数: {cycle["valid_hours_count"]:.2f}')
        print(f'跳过时间段:')
        
        # 计算时间差
        start = datetime.fromisoformat(cycle['start_date'])
        end = datetime.fromisoformat(cycle['end_date'])
        total_hours = (end - start).total_seconds() / 3600
        print(f'总时间差: {total_hours:.2f} 小时 ({total_hours/24:.2f} 天)')
        
        # 计算跳过时间
        total_skip = 0
        for skip in cycle.get('skip_period_records', []):
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
        if cycle["valid_days_count"] == 26:
            print('❌ 问题1: 有效天数为26天，但存在跳过时间段')
            print('   有效天数应该是: ', int(expected_valid / 24))
        
        if cycle["valid_hours_count"] > 700:
            print('❌ 问题2: 有效小时数过高')
            print(f'   {cycle["valid_hours_count"]:.2f}小时 = {cycle["valid_hours_count"]/24:.2f}天')
            print('   这超过了26天的理论最大值')
        
        break 