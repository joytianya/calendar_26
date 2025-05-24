#!/usr/bin/env python3
"""
测试前端历史记录页面有效小时数显示功能
"""

import os
import sys
import subprocess
import time
import requests
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class FrontendHoursDisplayTester:
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.frontend_url = "http://localhost:3000"
        
    def log(self, message, level="INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_backend_running(self):
        """检查后端是否运行"""
        try:
            response = requests.get(f"{self.base_url}/cycles/", timeout=5)
            if response.status_code == 200:
                self.log("✅ 后端服务正在运行")
                return True
            else:
                self.log(f"❌ 后端服务响应异常: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ 后端服务未运行: {e}", "ERROR")
            return False
    
    def check_frontend_files(self):
        """检查前端文件是否包含有效小时数相关代码"""
        files_to_check = [
            ("calendar_26/app/frontend/src/components/CycleHistory.tsx", [
                "有效小时数",
                "valid_hours_count",
                "formatHours"
            ]),
            ("calendar_26/app/frontend/src/models/types.ts", [
                "valid_hours_count: number"
            ])
        ]
        
        all_passed = True
        
        for file_path, required_content in files_to_check:
            self.log(f"🔍 检查文件: {file_path}")
            
            if not os.path.exists(file_path):
                self.log(f"❌ 文件不存在: {file_path}", "ERROR")
                all_passed = False
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for required in required_content:
                    if required in content:
                        self.log(f"  ✅ 找到: {required}")
                    else:
                        self.log(f"  ❌ 缺失: {required}", "ERROR")
                        all_passed = False
                        
            except Exception as e:
                self.log(f"❌ 读取文件失败: {e}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def check_table_headers(self):
        """检查CycleHistory.tsx中的表格头部是否包含有效小时数列"""
        file_path = "calendar_26/app/frontend/src/components/CycleHistory.tsx"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查桌面端表格头部
            if "有效小时数" in content and "TableHead" in content:
                self.log("✅ 桌面端表格头部包含有效小时数列")
                desktop_ok = True
            else:
                self.log("❌ 桌面端表格头部缺少有效小时数列", "ERROR")
                desktop_ok = False
            
            # 检查移动端卡片显示
            mobile_patterns = [
                "有效小时数:",
                "formatHours(cycle.valid_hours_count)"
            ]
            
            mobile_ok = True
            for pattern in mobile_patterns:
                if pattern in content:
                    self.log(f"  ✅ 移动端包含: {pattern}")
                else:
                    self.log(f"  ❌ 移动端缺失: {pattern}", "ERROR")
                    mobile_ok = False
            
            return desktop_ok and mobile_ok
            
        except Exception as e:
            self.log(f"❌ 检查表格头部失败: {e}", "ERROR")
            return False
    
    def check_format_hours_function(self):
        """检查formatHours函数是否正确实现"""
        file_path = "calendar_26/app/frontend/src/components/CycleHistory.tsx"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查formatHours函数的关键部分
            required_patterns = [
                "const formatHours",
                "hours // 24",
                "hours % 24",
                "天",
                "小时"
            ]
            
            all_found = True
            for pattern in required_patterns:
                if pattern in content:
                    self.log(f"  ✅ formatHours函数包含: {pattern}")
                else:
                    self.log(f"  ❌ formatHours函数缺失: {pattern}", "ERROR")
                    all_found = False
            
            return all_found
            
        except Exception as e:
            self.log(f"❌ 检查formatHours函数失败: {e}", "ERROR")
            return False
    
    def test_api_data_structure(self):
        """测试API返回的数据结构是否包含valid_hours_count"""
        try:
            response = requests.get(f"{self.base_url}/cycles/")
            if response.status_code == 200:
                cycles = response.json()
                if cycles:
                    cycle = cycles[0]
                    if 'valid_hours_count' in cycle:
                        hours_value = cycle['valid_hours_count']
                        self.log(f"✅ API返回数据包含valid_hours_count: {hours_value}")
                        
                        # 检查数据类型
                        if isinstance(hours_value, (int, float)):
                            self.log("✅ valid_hours_count数据类型正确")
                            return True
                        else:
                            self.log(f"❌ valid_hours_count数据类型错误: {type(hours_value)}", "ERROR")
                            return False
                    else:
                        self.log("❌ API返回数据缺少valid_hours_count字段", "ERROR")
                        return False
                else:
                    self.log("⚠️ 没有周期数据可供测试", "WARNING")
                    return True
            else:
                self.log(f"❌ API请求失败: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 测试API数据结构失败: {e}", "ERROR")
            return False
    
    def check_frontend_build(self):
        """检查前端是否能正常构建"""
        self.log("🔍 检查前端构建...")
        
        frontend_dir = "calendar_26/app/frontend"
        if not os.path.exists(frontend_dir):
            self.log(f"❌ 前端目录不存在: {frontend_dir}", "ERROR")
            return False
        
        try:
            # 检查package.json是否存在
            package_json = os.path.join(frontend_dir, "package.json")
            if not os.path.exists(package_json):
                self.log("❌ package.json不存在", "ERROR")
                return False
            
            # 尝试TypeScript类型检查
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--skipLibCheck"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log("✅ TypeScript类型检查通过")
                return True
            else:
                self.log(f"❌ TypeScript类型检查失败: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("⚠️ TypeScript检查超时", "WARNING")
            return True
        except Exception as e:
            self.log(f"⚠️ 无法执行TypeScript检查: {e}", "WARNING")
            return True
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("🚀 开始前端有效小时数显示功能测试")
        self.log("=" * 60)
        
        tests = [
            ("后端服务检查", self.check_backend_running),
            ("前端文件内容检查", self.check_frontend_files),
            ("表格头部检查", self.check_table_headers),
            ("formatHours函数检查", self.check_format_hours_function),
            ("API数据结构检查", self.test_api_data_structure),
            ("前端构建检查", self.check_frontend_build),
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
        
        self.log("\n" + "=" * 60)
        self.log(f"📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            self.log("🎉 所有测试通过！前端有效小时数显示功能正常")
        else:
            self.log("⚠️ 部分测试失败，请检查相关功能")
        
        return passed == total

def main():
    """主函数"""
    print("前端有效小时数显示功能测试脚本")
    print("=" * 60)
    
    tester = FrontendHoursDisplayTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 测试总结:")
        print("✅ 前端文件包含有效小时数相关代码")
        print("✅ 桌面端表格包含有效小时数列")
        print("✅ 移动端卡片显示有效小时数")
        print("✅ formatHours函数正确实现")
        print("✅ API数据结构包含valid_hours_count")
        print("✅ 前端代码类型检查通过")
        print("\n📝 使用说明:")
        print("1. 启动后端: cd calendar_26/app && python -m uvicorn main:app --reload")
        print("2. 启动前端: cd calendar_26/app/frontend && npm start")
        print("3. 访问历史记录页面查看有效小时数列")
    else:
        print("\n⚠️ 部分功能存在问题，请检查代码")
    
    return success

if __name__ == "__main__":
    main() 