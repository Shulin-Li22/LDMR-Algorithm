#!/usr/bin/env python3
"""
高级测试脚本
包含多场景测试、参数分析等高级功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / 'src'))

from config import load_scenario_config, switch_scenario
from runner import LDMRRunner, setup_logger


def run_multi_scenario_test():
    """运行多场景测试"""
    scenarios = ['testing', 'light_load', 'heavy_load', 'performance']
    
    print("🚀 开始多场景测试...")
    results = {}
    
    for scenario in scenarios:
        print(f"\n📊 运行场景: {scenario}")
        
        try:
            # 切换到指定场景
            config = load_scenario_config(scenario)
            logger = setup_logger(config.get('output', {}))
            
            # 运行仿真
            runner = LDMRRunner(config)
            result = runner.run()
            
            results[scenario] = result
            
        except Exception as e:
            print(f"❌ 场景 {scenario} 失败: {e}")
            results[scenario] = {'error': str(e)}
    
    print("\n✅ 多场景测试完成")
    return results


def run_parameter_analysis(parameter='r3', values=None):
    """运行参数敏感性分析"""
    if values is None:
        if parameter == 'r3':
            values = [30, 40, 50, 60, 70]
        elif parameter == 'K':
            values = [2, 3, 4]
        elif parameter == 'Ne_th':
            values = [1, 2, 3, 4]
        else:
            values = [1, 2, 3]
    
    print(f"🔬 开始参数分析: {parameter} = {values}")
    
    results = {}
    
    for value in values:
        print(f"\n🧪 测试 {parameter} = {value}")
        
        try:
            # 加载基础配置
            config = load_scenario_config('testing')  # 使用测试场景作为基础
            
            # 修改参数
            if parameter in ['K', 'r1', 'r2', 'r3', 'Ne_th']:
                config['algorithm']['config'][parameter] = value
            elif parameter == 'constellation':
                config['network']['constellation'] = value
            elif parameter == 'ground_stations':
                config['network']['ground_stations'] = value
            elif parameter == 'total_gbps':
                config['traffic']['total_gbps'] = value
            
            # 运行仿真
            logger = setup_logger(config.get('output', {}))
            runner = LDMRRunner(config)
            result = runner.run()
            
            # 提取关键指标
            stats = result.get('ldmr_statistics', {})
            results[value] = {
                'success_rate': stats.get('success_rate', 0),
                'avg_path_delay': stats.get('avg_path_delay', 0),
                'total_paths': stats.get('total_paths_calculated', 0),
                'avg_computation_time': stats.get('avg_computation_time', 0)
            }
            
            print(f"   结果: 成功率={results[value]['success_rate']:.2%}, "
                  f"延迟={results[value]['avg_path_delay']:.3f}ms")
            
        except Exception as e:
            print(f"❌ 参数 {parameter}={value} 失败: {e}")
            results[value] = {'error': str(e)}
    
    # 找到最优参数
    valid_results = {k: v for k, v in results.items() if 'error' not in v}
    if valid_results:
        best_value = max(valid_results.keys(), 
                        key=lambda x: valid_results[x]['success_rate'])
        print(f"\n🎯 最优参数: {parameter} = {best_value} "
              f"(成功率: {valid_results[best_value]['success_rate']:.2%})")
    
    print("\n✅ 参数分析完成")
    return results


def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "="*50)
        print("🎯 LDMR高级测试工具")
        print("="*50)
        print("1. 🧪 环境测试")
        print("2. 📊 多场景测试")
        print("3. 🔬 参数敏感性分析")
        print("4. 🔄 切换场景")
        print("5. 📋 查看配置")
        print("6. ❌ 退出")
        print("="*50)
        
        choice = input("请选择操作 (1-6): ").strip()
        
        if choice == '1':
            run_environment_test()
        elif choice == '2':
            run_multi_scenario_test()
        elif choice == '3':
            param = input("请输入参数名 (r3/K/Ne_th) [r3]: ").strip() or 'r3'
            run_parameter_analysis(param)
        elif choice == '4':
            switch_scenario_interactive()
        elif choice == '5':
            show_current_config()
        elif choice == '6':
            print("👋 退出程序")
            break
        else:
            print("❌ 无效选项，请重新选择")


def run_environment_test():
    """运行环境测试"""
    print("🧪 开始环境测试...")
    
    try:
        # 导入测试
        from topology.satellite_constellation import LEONetworkBuilder
        from traffic.traffic_model import TrafficGenerator
        from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig
        
        print("✅ 所有核心模块导入成功")
        
        # 创建小规模测试
        builder = LEONetworkBuilder('globalstar', 5)
        topology = builder.build_network()
        
        stats = topology.get_statistics()
        print(f"✅ 测试网络创建成功: {stats}")
        
        # 测试流量生成
        generator = TrafficGenerator()
        gs_list = [node.id for node in topology.nodes.values()
                   if node.type.value == 'ground_station']
        
        demands = generator.generate_traffic_demands(
            ground_station_ids=gs_list,
            total_traffic=2.0,
            duration=60.0
        )
        
        print(f"✅ 测试流量生成成功: {len(demands)} 个需求")
        
        # 测试LDMR算法
        config = LDMRConfig(K=2, r3=50)
        ldmr = LDMRAlgorithm(config)
        
        test_demands = demands[:5]
        results = ldmr.run_ldmr_algorithm(topology, test_demands)
        
        success_count = len([r for r in results if r.success])
        print(f"✅ LDMR算法测试成功: {success_count}/{len(test_demands)} 成功")
        
        print("🎉 环境测试完成 - 所有组件正常工作!")
        
    except Exception as e:
        print(f"❌ 环境测试失败: {e}")
        import traceback
        traceback.print_exc()


def switch_scenario_interactive():
    """交互式切换场景"""
    scenarios = ['testing', 'light_load', 'heavy_load', 'performance']
    
    print("\n可用场景:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario}")
    
    try:
        choice = input("请选择场景 (1-4): ").strip()
        scenario_index = int(choice) - 1
        
        if 0 <= scenario_index < len(scenarios):
            scenario = scenarios[scenario_index]
            switch_scenario(scenario)
            print(f"✅ 已切换到场景: {scenario}")
        else:
            print("❌ 无效选择")
            
    except ValueError:
        print("❌ 请输入有效数字")


def show_current_config():
    """显示当前配置"""
    from config import load_default_config
    
    config = load_default_config()
    
    print("\n📋 当前配置:")
    print(f"  仿真名称: {config['simulation']['name']}")
    print(f"  星座类型: {config['network']['constellation']}")
    print(f"  地面站数: {config['network']['ground_stations']}")
    print(f"  总流量: {config['traffic']['total_gbps']} Gbps")
    print(f"  仿真时长: {config['traffic']['duration']} 秒")
    print(f"  算法K值: {config['algorithm']['config']['K']}")
    print(f"  算法r3值: {config['algorithm']['config']['r3']}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'multi-scenario':
            run_multi_scenario_test()
        elif command == 'param-analysis':
            param = sys.argv[2] if len(sys.argv) > 2 else 'r3'
            run_parameter_analysis(param)
        elif command == 'env-test':
            run_environment_test()
        else:
            print(f"❌ 未知命令: {command}")
            print("支持的命令: multi-scenario, param-analysis, env-test")
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
