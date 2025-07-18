#!/usr/bin/env python3
"""
快速测试脚本
验证简化版本是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir / 'src'))

def test_imports():
    """测试导入"""
    print("🧪 测试模块导入...")
    
    try:
        # 测试PyYAML
        import yaml
        print("✅ yaml - 导入成功")
        
        # 测试配置模块
        from config.config_loader import ConfigLoader
        print("✅ ConfigLoader - 导入成功")
        
        from config.validator import ConfigValidator
        print("✅ ConfigValidator - 导入成功")
        
        # 测试运行器模块
        from runner.ldmr_runner import LDMRRunner
        print("✅ LDMRRunner - 导入成功")
        
        from runner.result_handler import ResultHandler
        print("✅ ResultHandler - 导入成功")
        
        from runner.logger import get_logger
        print("✅ Logger - 导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n🧪 测试配置加载...")
    
    try:
        from config import load_default_config
        
        config = load_default_config()
        print("✅ 默认配置加载成功")
        
        # 检查关键配置项
        assert 'simulation' in config
        assert 'network' in config
        assert 'algorithm' in config
        assert 'traffic' in config
        print("✅ 配置结构验证成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_directories():
    """测试目录结构"""
    print("\n🧪 测试目录结构...")
    
    required_dirs = [
        'config',
        'config/scenarios',
        'src/config',
        'src/runner',
        'scripts',
        'results',
        'logs'
    ]
    
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            print(f"❌ 目录缺失: {dir_name}")
        else:
            print(f"✅ 目录存在: {dir_name}")
    
    if missing_dirs:
        print(f"\n请运行: python setup.py")
        return False
    
    return True

def test_config_files():
    """测试配置文件"""
    print("\n🧪 测试配置文件...")
    
    required_files = [
        'config/default_config.yaml',
        'config/scenarios/testing.yaml',
        'config/scenarios/performance.yaml'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = Path(file_name)
        if not file_path.exists():
            missing_files.append(file_name)
            print(f"❌ 文件缺失: {file_name}")
        else:
            print(f"✅ 文件存在: {file_name}")
    
    return len(missing_files) == 0

def main():
    """主测试函数"""
    print("🚀 LDMR简化版本快速测试")
    print("=" * 50)
    
    all_passed = True
    
    # 测试目录结构
    if not test_directories():
        all_passed = False
    
    # 测试配置文件
    if not test_config_files():
        all_passed = False
    
    # 测试导入
    if not test_imports():
        all_passed = False
    
    # 测试配置加载
    if not test_config_loading():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！")
        print("\n📋 下一步:")
        print("   python main_simple.py")
        return True
    else:
        print("❌ 部分测试失败")
        print("\n🔧 修复建议:")
        print("   1. 运行: python setup.py")
        print("   2. 检查依赖: pip install pyyaml numpy pandas matplotlib networkx scipy")
        print("   3. 重新测试: python quick_test.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
