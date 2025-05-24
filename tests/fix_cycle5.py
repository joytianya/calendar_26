#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# 获取周期5的详细信息
response = requests.get("http://localhost:8000/api/cycles/")
cycles = response.json()

cycle5 = None
for cycle in cycles:
    if cycle['cycle_number'] == 5:
        cycle5 = cycle
        break

if not cycle5:
    print("未找到周期5")
    exit(1)

print("周期5当前信息:")
print(f"ID: {cycle5['id']}")
print(f"开始时间: {cycle5['start_date']}")
print(f"结束时间: {cycle5['end_date']}")
print(f"有效天数: {cycle5['valid_days_count']}")
print(f"有效小时数: {cycle5['valid_hours_count']:.2f}")
print()

# 尝试通过编辑API触发重新计算
print("触发重新计算...")
update_data = {
    "start_date": cycle5['start_date'],
    "remark": cycle5.get('remark', '') + " [手动触发重新计算]"
}

if cycle5['end_date']:
    update_data['end_date'] = cycle5['end_date']

response = requests.put(f"http://localhost:8000/api/cycles/{cycle5['id']}", json=update_data)

if response.status_code == 200:
    updated_cycle = response.json()
    print("重新计算成功！")
    print(f"新有效天数: {updated_cycle['valid_days_count']}")
    print(f"新有效小时数: {updated_cycle['valid_hours_count']:.2f}")
    
    # 计算预期值
    start = datetime.fromisoformat(updated_cycle['start_date'])
    end = datetime.now() if not updated_cycle['end_date'] else datetime.fromisoformat(updated_cycle['end_date'])
    expected_hours = (end - start).total_seconds() / 3600
    print(f"预期有效小时数: {expected_hours:.2f}")
    
    if abs(updated_cycle['valid_hours_count'] - expected_hours) > 0.1:
        print("❌ 重新计算后仍有问题")
    else:
        print("✅ 重新计算成功")
else:
    print(f"重新计算失败: {response.status_code} - {response.text}")

print("\n如果你看到的时间是 2025/05/23 17:45 到 2025/05/24 05:48")
print("那么可能是前端显示格式的问题，或者数据不同步")
print("实际数据库中的时间如上所示") 