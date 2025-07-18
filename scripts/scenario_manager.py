#!/usr/bin/env python3
"""
场景管理工具
用于切换和管理仿真场景
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / 'src'))

try:
    from config import get_config_loader, load_default_config
except ImportError:
    # 如果直接导入失败，尝试从相对路径导入
    import sys
    sys.path.append('../src')
    from config import get_config_loader, load_default_config


def list_scenarios():
    """列出所有可用场景"""
    loader = get_config_loader()
    scenarios = loader.list_available_scenarios()
    
    print("📋 可用场景:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario}")
    
    return scenarios


def switch_scenario(scenario_name):
    """切换到指定场景"""
    loader = get_config_loader()
    
    # 检查场景是否存在
    available_scenarios = loader.list_available_scenarios()
    if scenario_name not in available_scenarios:
        print(f"❌ 场景 '{scenario_name}' 不存在")
        print(f"可用场景: {', '.join(available_scenarios)}")
        return False
    
    try:
        # 切换场景
        loader.save_current_scenario(scenario_name)
        print(f"✅ 已切换到场景: {scenario_name}")
        
        # 显示场景配置
        config = loader.load_complete_config()
        print(f"   星座类型: {config['network']['constellation']}")
        print(f"   地面站数: {config['network']['ground_stations']}")
        print(f"   总流量: {config['traffic']['total_gbps']} Gbps")
        print(f"   仿真时长: {config['traffic']['duration']} 秒")
        
        return True
        
    except Exception as e:
        print(f"❌ 切换场景失败: {e}")
        return False


def show_current_scenario():
    """显示当前场景配置"""
    loader = get_config_loader()
    
    # 检查是否有当前场景
    if not loader.current_scenario_path.exists():
        print("📋 当前使用默认配置")
    else:
        current_config = loader.load_current_scenario()
        if current_config:
            print("📋 当前场景配置:")
            if 'simulation' in current_config:
                print(f"   名称: {current_config['simulation'].get('name', 'N/A')}")
        else:
            print("📋 当前使用默认配置")
    
    # 显示完整配置
    config = load_default_config()
    print("\n📊 当前有效配置:")
    print(f"   仿真名称: {config['simulation']['name']}")
    print(f"   星座类型: {config['network']['constellation']}")
    print(f"   地面站数: {config['network']['ground_stations']}")
    print(f"   总流量: {config['traffic']['total_gbps']} Gbps")
    print(f"   仿真时长: {config['traffic']['duration']} 秒")
    print(f"   算法K值: {config['algorithm']['config']['K']}")
    print(f"   算法r3值: {config['algorithm']['config']['r3']}")


def reset_to_default():
    """重置到默认配置"""
    loader = get_config_loader()
    
    try:
        # 删除当前场景文件
        if loader.current_scenario_path.exists():
            loader.current_scenario_path.unlink()
            print("✅ 已重置到默认配置")
        else:
            print("ℹ️  当前已经是默认配置")
            
    except Exception as e:
        print(f"❌ 重置失败: {e}")


def interactive_scenario_manager():
    """交互式场景管理器"""
    while True:
        print("\n" + "="*40)
        print("🎯 场景管理器")
        print("="*40)
        print("1. 📋 列出所有场景")
        print("2. 🔄 切换场景")
        print("3. 📊 显示当前配置")
        print("4. 🔙 重置到默认配置")
        print("5. ❌ 退出")
        print("="*40)
        
        choice = input("请选择操作 (1-5): ").strip()
        
        if choice == '1':
            list_scenarios()
        elif choice == '2':
            scenarios = list_scenarios()
            if scenarios:
                try:
                    idx = int(input("请选择场景编号: ")) - 1
                    if 0 <= idx < len(scenarios):
                        switch_scenario(scenarios[idx])
                    else:
                        print("❌ 无效编号")
                except ValueError:
                    print("❌ 请输入有效数字")
        elif choice == '3':
            show_current_scenario()
        elif choice == '4':
            reset_to_default()
        elif choice == '5':
            print("👋 退出")
            break
        else:
            print("❌ 无效选项")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        interactive_scenario_manager()
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        list_scenarios()
    elif command == 'switch':
        if len(sys.argv) < 3:
            print("❌ 请指定场景名称")
            print("用法: python scenario_manager.py switch <scenario_name>")
            return
        scenario_name = sys.argv[2]
        switch_scenario(scenario_name)
    elif command == 'show':
        show_current_scenario()
    elif command == 'reset':
        reset_to_default()
    elif command == 'interactive':
        interactive_scenario_manager()
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令:")
        print("  list      - 列出所有场景")
        print("  switch    - 切换场景")
        print("  show      - 显示当前配置")
        print("  reset     - 重置到默认配置")
        print("  interactive - 交互式模式")


if __name__ == "__main__":
    main()
