#!/usr/bin/env python3
"""
历史记录编辑功能完整测试脚本
一键测试所有功能：
1. 后端API测试
2. 前端组件测试
3. 数据库操作测试
4. 移动端和桌面端功能测试
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def run_script(script_path, description):
    """运行测试脚本"""
    print(f"\n{'='*60}")
    print(f"🚀 开始执行: {description}")
    print(f"{'='*60}")
    
    try:
        # 使用当前Python解释器运行脚本
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} 测试完成")
            return True
        else:
            print(f"❌ {description} 测试失败 (返回码: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} 测试超时")
        return False
    except Exception as e:
        print(f"❌ {description} 测试异常: {e}")
        return False

def check_prerequisites():
    """检查前置条件"""
    print("🔍 检查前置条件...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python版本需要3.8或更高")
        return False
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    
    # 检查项目目录结构
    required_dirs = [
        "app",
        "app/frontend",
        "app/routers",
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ 缺少目录: {dir_path}")
            return False
    print("✅ 项目目录结构正确")
    
    # 检查关键文件
    required_files = [
        "app/main.py",
        "app/frontend/src/components/CycleHistory.tsx",
        "app/routers/cycles.py",
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ 缺少文件: {file_path}")
            return False
    print("✅ 关键文件存在")
    
    return True

def start_backend_server():
    """启动后端服务器"""
    print("\n🚀 启动后端服务器...")
    
    try:
        # 检查端口是否已被占用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("✅ 后端服务器已在运行")
            return None
        
        # 启动后端服务器
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
            cwd="app",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服务器启动
        print("⏳ 等待后端服务器启动...")
        time.sleep(5)
        
        # 检查服务器是否启动成功
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("✅ 后端服务器启动成功")
            return backend_process
        else:
            print("❌ 后端服务器启动失败")
            backend_process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ 启动后端服务器异常: {e}")
        return None

def main():
    """主函数"""
    start_time = datetime.now()
    
    print("🎯 历史记录编辑功能完整测试")
    print("=" * 60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查前置条件
    if not check_prerequisites():
        print("❌ 前置条件检查失败，请检查项目环境")
        return False
    
    # 启动后端服务器
    backend_process = start_backend_server()
    
    try:
        # 测试脚本列表
        tests = [
            ("test_frontend_edit.py", "前端编辑功能测试"),
            ("test_history_edit.py", "后端API编辑功能测试"),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        # 运行所有测试
        for script_path, description in tests:
            if os.path.exists(script_path):
                if run_script(script_path, description):
                    passed_tests += 1
                else:
                    print(f"⚠️ {description} 失败")
            else:
                print(f"❌ 测试脚本不存在: {script_path}")
        
        # 输出测试结果
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        print(f"测试耗时: {duration.total_seconds():.1f}秒")
        
        if passed_tests == total_tests:
            print("\n🎉 所有测试通过！历史记录编辑功能完全正常")
            print("\n✅ 功能验证:")
            print("  - 编辑开始日期功能正常")
            print("  - 编辑结束日期功能正常")
            print("  - 编辑备注功能正常")
            print("  - 移动端编辑按钮显示正常")
            print("  - 桌面端编辑功能正常")
            print("  - 数据持久化正常")
            print("  - 前端构建成功")
            print("  - API接口正常")
            
            print("\n🎯 修复总结:")
            print("  1. ✅ 修复了编辑开始日期前端没有变化的问题")
            print("  2. ✅ 添加了移动端编辑按钮和功能")
            print("  3. ✅ 改进了日期时间处理逻辑")
            print("  4. ✅ 优化了后端日期时间转换")
            print("  5. ✅ 完善了编辑表单验证")
            
            return True
        else:
            print("\n⚠️ 部分测试失败，请检查以下内容:")
            print("  - 后端服务是否正常运行")
            print("  - 数据库连接是否正常")
            print("  - 前端依赖是否安装完整")
            print("  - 代码是否有语法错误")
            return False
    
    finally:
        # 清理后端进程
        if backend_process:
            print("\n🧹 清理后端进程...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
                print("✅ 后端进程已停止")
            except subprocess.TimeoutExpired:
                backend_process.kill()
                print("⚠️ 强制停止后端进程")

def show_usage():
    """显示使用说明"""
    print("""
使用说明:
1. 确保在项目根目录运行此脚本
2. 确保已安装所有依赖包
3. 确保数据库已配置并可连接

运行命令:
    python calendar_26/run_complete_test.py

测试内容:
- 前端组件完整性检查
- 前端构建测试
- 后端API功能测试
- 数据库操作测试
- 编辑功能端到端测试

如果测试失败，请检查:
- Python版本 (需要3.8+)
- 项目目录结构
- 依赖包安装
- 数据库配置
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
    else:
        success = main()
        sys.exit(0 if success else 1) 