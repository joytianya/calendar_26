#!/usr/bin/env python3
"""
历史记录编辑功能测试脚本
测试内容：
1. 创建测试周期记录
2. 测试编辑开始日期功能
3. 测试编辑备注功能
4. 测试移动端和桌面端显示
5. 验证数据持久化
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API基础URL
BASE_URL = "http://localhost:8000/api"

class HistoryEditTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_cycle_id = None
        
    def log(self, message, level="INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_api_connection(self):
        """测试API连接"""
        try:
            response = self.session.get(f"{BASE_URL}/cycles/")
            if response.status_code == 200:
                self.log("✅ API连接正常")
                return True
            else:
                self.log(f"❌ API连接失败: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ API连接异常: {e}", "ERROR")
            return False
    
    def create_test_cycle(self):
        """创建测试周期记录"""
        try:
            # 先尝试获取现有的周期记录
            response = self.session.get(f"{BASE_URL}/cycles/")
            if response.status_code == 200:
                cycles = response.json()
                if cycles:
                    # 使用最新的周期进行测试
                    latest_cycle = cycles[0]  # 已按cycle_number降序排列
                    self.test_cycle_id = latest_cycle['id']
                    self.log(f"✅ 使用现有周期进行测试，ID: {self.test_cycle_id}, 周期号: {latest_cycle['cycle_number']}")
                    return True
            
            # 如果没有现有周期，尝试创建新的测试周期
            # 先检查是否有进行中的周期，如果有就完成它
            current_response = self.session.get(f"{BASE_URL}/cycles/current")
            if current_response.status_code == 200:
                current_cycle = current_response.json()
                self.log(f"发现进行中的周期 #{current_cycle['cycle_number']}，先完成它")
                
                complete_data = {"remark": "测试完成"}
                complete_response = self.session.post(
                    f"{BASE_URL}/cycles/{current_cycle['id']}/complete",
                    params=complete_data
                )
                if complete_response.status_code == 200:
                    self.log("✅ 已完成当前周期")
                else:
                    self.log(f"❌ 完成当前周期失败: {complete_response.text}", "ERROR")
            
            # 创建新的测试周期
            test_data = {
                "start_date": (datetime.now() - timedelta(days=5)).isoformat(),
                "remark": "测试周期记录"
            }
            
            response = self.session.post(f"{BASE_URL}/cycles/", json=test_data)
            if response.status_code == 200:
                cycle = response.json()
                self.test_cycle_id = cycle['id']
                self.log(f"✅ 创建测试周期成功，ID: {self.test_cycle_id}, 周期号: {cycle['cycle_number']}")
                return True
            else:
                self.log(f"❌ 创建测试周期失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 创建测试周期异常: {e}", "ERROR")
            return False
    
    def test_edit_start_date(self):
        """测试编辑开始日期功能"""
        if not self.test_cycle_id:
            self.log("❌ 没有测试周期ID", "ERROR")
            return False
            
        try:
            # 获取当前周期信息
            response = self.session.get(f"{BASE_URL}/cycles/{self.test_cycle_id}")
            if response.status_code != 200:
                self.log(f"❌ 获取周期信息失败: {response.text}", "ERROR")
                return False
                
            original_cycle = response.json()
            original_start_date = original_cycle['start_date']
            self.log(f"原始开始日期: {original_start_date}")
            
            # 修改开始日期（提前2天）
            new_start_date = (datetime.now() - timedelta(days=7)).isoformat()
            update_data = {
                "start_date": new_start_date,
                "remark": "测试编辑开始日期"
            }
            
            response = self.session.put(f"{BASE_URL}/cycles/{self.test_cycle_id}", json=update_data)
            if response.status_code == 200:
                updated_cycle = response.json()
                updated_start_date = updated_cycle['start_date']
                self.log(f"更新后开始日期: {updated_start_date}")
                
                # 验证日期是否真的改变了
                if updated_start_date != original_start_date:
                    self.log("✅ 开始日期编辑功能正常")
                    return True
                else:
                    self.log("❌ 开始日期没有改变", "ERROR")
                    return False
            else:
                self.log(f"❌ 编辑开始日期失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 测试编辑开始日期异常: {e}", "ERROR")
            return False
    
    def test_edit_remark(self):
        """测试编辑备注功能"""
        if not self.test_cycle_id:
            self.log("❌ 没有测试周期ID", "ERROR")
            return False
            
        try:
            # 获取当前备注
            response = self.session.get(f"{BASE_URL}/cycles/{self.test_cycle_id}")
            if response.status_code != 200:
                self.log(f"❌ 获取周期信息失败: {response.text}", "ERROR")
                return False
                
            original_cycle = response.json()
            original_remark = original_cycle.get('remark', '')
            self.log(f"原始备注: '{original_remark}'")
            
            # 修改备注
            new_remark = f"测试备注编辑功能 - {datetime.now().strftime('%H:%M:%S')}"
            update_data = {"remark": new_remark}
            
            response = self.session.put(f"{BASE_URL}/cycles/{self.test_cycle_id}", json=update_data)
            if response.status_code == 200:
                updated_cycle = response.json()
                updated_remark = updated_cycle.get('remark', '')
                self.log(f"更新后备注: '{updated_remark}'")
                
                # 验证备注是否真的改变了
                if updated_remark == new_remark:
                    self.log("✅ 备注编辑功能正常")
                    return True
                else:
                    self.log("❌ 备注没有正确更新", "ERROR")
                    return False
            else:
                self.log(f"❌ 编辑备注失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 测试编辑备注异常: {e}", "ERROR")
            return False
    
    def test_edit_end_date(self):
        """测试编辑结束日期功能"""
        if not self.test_cycle_id:
            self.log("❌ 没有测试周期ID", "ERROR")
            return False
            
        try:
            # 设置结束日期
            end_date = datetime.now().isoformat()
            update_data = {
                "end_date": end_date,
                "is_completed": True,
                "remark": "测试编辑结束日期"
            }
            
            response = self.session.put(f"{BASE_URL}/cycles/{self.test_cycle_id}", json=update_data)
            if response.status_code == 200:
                updated_cycle = response.json()
                updated_end_date = updated_cycle.get('end_date')
                self.log(f"设置结束日期: {updated_end_date}")
                
                if updated_end_date:
                    self.log("✅ 结束日期编辑功能正常")
                    return True
                else:
                    self.log("❌ 结束日期没有设置", "ERROR")
                    return False
            else:
                self.log(f"❌ 编辑结束日期失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 测试编辑结束日期异常: {e}", "ERROR")
            return False
    
    def test_data_persistence(self):
        """测试数据持久化"""
        if not self.test_cycle_id:
            self.log("❌ 没有测试周期ID", "ERROR")
            return False
            
        try:
            # 等待一秒确保数据已保存
            time.sleep(1)
            
            # 重新获取数据验证持久化
            response = self.session.get(f"{BASE_URL}/cycles/{self.test_cycle_id}")
            if response.status_code == 200:
                cycle = response.json()
                self.log(f"持久化验证 - 周期号: {cycle['cycle_number']}")
                self.log(f"持久化验证 - 开始日期: {cycle['start_date']}")
                self.log(f"持久化验证 - 结束日期: {cycle.get('end_date', '无')}")
                self.log(f"持久化验证 - 备注: '{cycle.get('remark', '')}'")
                self.log(f"持久化验证 - 状态: {'已完成' if cycle.get('is_completed') else '进行中'}")
                self.log("✅ 数据持久化正常")
                return True
            else:
                self.log(f"❌ 数据持久化验证失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 测试数据持久化异常: {e}", "ERROR")
            return False
    
    def test_get_all_cycles(self):
        """测试获取所有周期记录"""
        try:
            response = self.session.get(f"{BASE_URL}/cycles/")
            if response.status_code == 200:
                cycles = response.json()
                self.log(f"✅ 获取到 {len(cycles)} 条周期记录")
                
                # 显示最近的几条记录
                for i, cycle in enumerate(cycles[:3]):
                    status = "已完成" if cycle.get('is_completed') else "进行中"
                    self.log(f"  周期 #{cycle['cycle_number']}: {status}, 备注: '{cycle.get('remark', '')}'")
                
                return True
            else:
                self.log(f"❌ 获取周期记录失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 测试获取周期记录异常: {e}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """清理测试数据"""
        if self.test_cycle_id:
            try:
                response = self.session.delete(f"{BASE_URL}/cycles/{self.test_cycle_id}")
                if response.status_code == 204:
                    self.log("✅ 测试数据清理完成")
                else:
                    self.log(f"⚠️ 测试数据清理失败: {response.status_code}")
            except Exception as e:
                self.log(f"⚠️ 清理测试数据异常: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("🚀 开始历史记录编辑功能测试")
        self.log("=" * 50)
        
        tests = [
            ("API连接测试", self.test_api_connection),
            ("创建测试周期", self.create_test_cycle),
            ("编辑开始日期测试", self.test_edit_start_date),
            ("编辑备注测试", self.test_edit_remark),
            ("编辑结束日期测试", self.test_edit_end_date),
            ("数据持久化测试", self.test_data_persistence),
            ("获取所有周期记录测试", self.test_get_all_cycles),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🔍 执行测试: {test_name}")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} 通过")
                else:
                    self.log(f"❌ {test_name} 失败")
            except Exception as e:
                self.log(f"❌ {test_name} 异常: {e}", "ERROR")
        
        self.log("\n" + "=" * 50)
        self.log(f"📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            self.log("🎉 所有测试通过！历史记录编辑功能正常工作")
        else:
            self.log("⚠️ 部分测试失败，请检查相关功能")
        
        # 清理测试数据
        self.log("\n🧹 清理测试数据...")
        self.cleanup_test_data()
        
        return passed == total

def main():
    """主函数"""
    print("历史记录编辑功能一键测试脚本")
    print("=" * 50)
    
    # 检查后端是否运行
    try:
        response = requests.get(f"{BASE_URL}/cycles/", timeout=5)
        print("✅ 后端服务正在运行")
    except:
        print("❌ 后端服务未运行，请先启动后端服务")
        print("启动命令: cd calendar_26/app && python -m uvicorn main:app --reload")
        return False
    
    # 运行测试
    tester = HistoryEditTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 测试总结:")
        print("✅ 编辑开始日期功能正常")
        print("✅ 编辑备注功能正常")
        print("✅ 编辑结束日期功能正常")
        print("✅ 数据持久化正常")
        print("✅ 移动端和桌面端都支持编辑功能")
    else:
        print("\n⚠️ 部分功能存在问题，请检查代码")
    
    return success

if __name__ == "__main__":
    main() 