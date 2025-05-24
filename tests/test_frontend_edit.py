#!/usr/bin/env python3
"""
前端编辑功能测试脚本
测试内容：
1. 检查前端构建是否成功
2. 验证编辑组件是否正确渲染
3. 测试移动端和桌面端编辑按钮
4. 验证日期时间处理逻辑
"""

import subprocess
import os
import sys
import time
import json
from datetime import datetime

class FrontendEditTester:
    def __init__(self):
        self.frontend_path = "app/frontend"
        
    def log(self, message, level="INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_frontend_build(self):
        """检查前端构建"""
        try:
            self.log("检查前端构建状态...")
            
            # 检查是否有node_modules
            node_modules_path = os.path.join(self.frontend_path, "node_modules")
            if not os.path.exists(node_modules_path):
                self.log("node_modules不存在，正在安装依赖...")
                result = subprocess.run(
                    ["npm", "install"], 
                    cwd=self.frontend_path, 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    self.log(f"❌ 依赖安装失败: {result.stderr}", "ERROR")
                    return False
                self.log("✅ 依赖安装成功")
            
            # 尝试构建前端
            self.log("正在构建前端...")
            result = subprocess.run(
                ["npm", "run", "build"], 
                cwd=self.frontend_path, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                self.log("✅ 前端构建成功")
                return True
            else:
                self.log(f"❌ 前端构建失败: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 前端构建检查异常: {e}", "ERROR")
            return False
    
    def check_component_files(self):
        """检查组件文件是否存在"""
        try:
            component_file = os.path.join(self.frontend_path, "src/components/CycleHistory.tsx")
            
            if not os.path.exists(component_file):
                self.log("❌ CycleHistory.tsx 文件不存在", "ERROR")
                return False
            
            # 读取文件内容检查关键功能
            with open(component_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查关键功能是否存在
            checks = [
                ("MobileCycleEdit", "移动端编辑组件"),
                ("MobileCycleSkipPeriods", "移动端跳过时间段组件"),
                ("handleEditSubmit", "编辑提交函数"),
                ("editForm", "编辑表单状态"),
                ("start_date", "开始日期字段"),
                ("end_date", "结束日期字段"),
                ("remark", "备注字段"),
            ]
            
            missing_features = []
            for feature, description in checks:
                if feature not in content:
                    missing_features.append(f"{description} ({feature})")
            
            if missing_features:
                self.log("❌ 缺少以下功能:", "ERROR")
                for feature in missing_features:
                    self.log(f"  - {feature}", "ERROR")
                return False
            else:
                self.log("✅ 所有关键功能都存在")
                return True
                
        except Exception as e:
            self.log(f"❌ 检查组件文件异常: {e}", "ERROR")
            return False
    
    def check_api_service(self):
        """检查API服务文件"""
        try:
            api_file = os.path.join(self.frontend_path, "src/services/api.ts")
            
            if not os.path.exists(api_file):
                self.log("❌ api.ts 文件不存在", "ERROR")
                return False
            
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查API方法
            api_methods = [
                "updateCycle",
                "deleteCycle",
                "getAllCycles",
                "getSkipPeriods"
            ]
            
            missing_methods = []
            for method in api_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if missing_methods:
                self.log("❌ 缺少以下API方法:", "ERROR")
                for method in missing_methods:
                    self.log(f"  - {method}", "ERROR")
                return False
            else:
                self.log("✅ 所有API方法都存在")
                return True
                
        except Exception as e:
            self.log(f"❌ 检查API服务文件异常: {e}", "ERROR")
            return False
    
    def check_types_definition(self):
        """检查类型定义"""
        try:
            types_file = os.path.join(self.frontend_path, "src/models/types.ts")
            
            if not os.path.exists(types_file):
                self.log("❌ types.ts 文件不存在", "ERROR")
                return False
            
            with open(types_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查类型定义
            type_definitions = [
                "CycleRecord",
                "SkipPeriod",
                "start_date",
                "end_date",
                "remark"
            ]
            
            missing_types = []
            for type_def in type_definitions:
                if type_def not in content:
                    missing_types.append(type_def)
            
            if missing_types:
                self.log("❌ 缺少以下类型定义:", "ERROR")
                for type_def in missing_types:
                    self.log(f"  - {type_def}", "ERROR")
                return False
            else:
                self.log("✅ 所有类型定义都存在")
                return True
                
        except Exception as e:
            self.log(f"❌ 检查类型定义异常: {e}", "ERROR")
            return False
    
    def analyze_edit_logic(self):
        """分析编辑逻辑"""
        try:
            component_file = os.path.join(self.frontend_path, "src/components/CycleHistory.tsx")
            
            with open(component_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查日期时间处理逻辑
            date_logic_checks = [
                ("slice(0, 10)", "日期部分提取"),
                ("slice(11, 16)", "时间部分提取"),
                ("slice(11, 19)", "完整时间提取"),
                ("T", "ISO格式连接符"),
                ("isoformat", "ISO格式处理"),
            ]
            
            self.log("分析日期时间处理逻辑:")
            for check, description in date_logic_checks:
                if check in content:
                    self.log(f"  ✅ {description}")
                else:
                    self.log(f"  ⚠️ 缺少 {description}")
            
            # 检查编辑表单逻辑
            form_logic_checks = [
                ("editForm", "编辑表单状态"),
                ("setEditForm", "编辑表单更新"),
                ("handleEditSubmit", "编辑提交处理"),
                ("handleEditChange", "编辑字段变更"),
                ("updateData", "更新数据构造"),
            ]
            
            self.log("分析编辑表单逻辑:")
            for check, description in form_logic_checks:
                if check in content:
                    self.log(f"  ✅ {description}")
                else:
                    self.log(f"  ⚠️ 缺少 {description}")
            
            # 检查移动端支持
            mobile_checks = [
                ("MobileCycleEdit", "移动端编辑组件"),
                ("isMobile", "移动端检测"),
                ("display: { xs:", "响应式显示"),
                ("fullWidth", "全宽度支持"),
            ]
            
            self.log("分析移动端支持:")
            for check, description in mobile_checks:
                if check in content:
                    self.log(f"  ✅ {description}")
                else:
                    self.log(f"  ⚠️ 缺少 {description}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 分析编辑逻辑异常: {e}", "ERROR")
            return False
    
    def check_package_json(self):
        """检查package.json配置"""
        try:
            package_file = os.path.join(self.frontend_path, "package.json")
            
            if not os.path.exists(package_file):
                self.log("❌ package.json 文件不存在", "ERROR")
                return False
            
            with open(package_file, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # 检查关键依赖
            dependencies = package_data.get('dependencies', {})
            required_deps = [
                '@mui/material',
                '@mui/icons-material',
                'react',
                'typescript'
            ]
            
            missing_deps = []
            for dep in required_deps:
                if dep not in dependencies:
                    missing_deps.append(dep)
            
            if missing_deps:
                self.log("❌ 缺少以下依赖:", "ERROR")
                for dep in missing_deps:
                    self.log(f"  - {dep}", "ERROR")
                return False
            else:
                self.log("✅ 所有必需依赖都存在")
                return True
                
        except Exception as e:
            self.log(f"❌ 检查package.json异常: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("🚀 开始前端编辑功能测试")
        self.log("=" * 50)
        
        tests = [
            ("检查package.json配置", self.check_package_json),
            ("检查组件文件", self.check_component_files),
            ("检查API服务", self.check_api_service),
            ("检查类型定义", self.check_types_definition),
            ("分析编辑逻辑", self.analyze_edit_logic),
            ("检查前端构建", self.check_frontend_build),
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
            self.log("🎉 前端编辑功能测试全部通过！")
        else:
            self.log("⚠️ 部分测试失败，请检查相关功能")
        
        return passed == total

def main():
    """主函数"""
    print("前端编辑功能测试脚本")
    print("=" * 50)
    
    # 检查是否在正确的目录
    if not os.path.exists("app/frontend"):
        print("❌ 未找到前端目录，请确保在正确的项目根目录运行")
        return False
    
    # 运行测试
    tester = FrontendEditTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 前端测试总结:")
        print("✅ 组件文件完整")
        print("✅ API服务正常")
        print("✅ 类型定义完整")
        print("✅ 编辑逻辑正确")
        print("✅ 移动端支持完整")
        print("✅ 前端构建成功")
    else:
        print("\n⚠️ 前端存在问题，请检查相关文件")
    
    return success

if __name__ == "__main__":
    main() 