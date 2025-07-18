#!/usr/bin/env python3
"""
基准测试脚本
运行LDMR与其他算法的性能对比
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / 'src'))

from topology.satellite_constellation import LEONetworkBuilder
from traffic.traffic_model import TrafficGenerator
from algorithms.baseline import BenchmarkManager
from config import load_scenario_config
from runner import setup_logger


def run_single_scenario_benchmark(scenario_name: str = 'testing'):
    """运行单场景基准测试"""
    print(f"🔬 开始基准测试 - 场景: {scenario_name}")
    print("=" * 60)
    
    try:
        # 加载场景配置
        config = load_scenario_config(scenario_name)
        logger = setup_logger(config.get('output', {}))
        
        # 构建网络拓扑
        print("🔧 构建网络拓扑...")
        network_config = config['network']
        builder = LEONetworkBuilder(
            network_config['constellation'], 
            network_config['ground_stations']
        )
        topology = builder.build_network()
        
        network_stats = topology.get_statistics()
        print(f"   网络: {network_stats['total_nodes']}节点, {network_stats['total_links']}链路")
        
        # 生成流量需求
        print("📈 生成流量需求...")
        traffic_config = config['traffic']
        generator = TrafficGenerator()
        
        ground_stations = [
            node.id for node in topology.nodes.values()
            if node.type.value == 'ground_station'
        ]
        
        demands = generator.generate_traffic_demands(
            ground_station_ids=ground_stations,
            total_traffic=traffic_config['total_gbps'],
            duration=traffic_config['duration'],
            elephant_ratio=traffic_config['elephant_ratio']
        )
        
        print(f"   生成 {len(demands)} 个流量需求")
        
        # 运行基准测试
        print("\n🚀 开始算法对比...")
        manager = BenchmarkManager()
        
        # 运行所有算法
        results = manager.run_benchmark(topology, demands, ['LDMR', 'SPF', 'ECMP'])
        
        # 显示结果
        print("\n📊 基准测试结果:")
        print(manager.generate_comparison_table(results))
        
        # 保存结果
        result_files = manager.save_results(results, config['output']['results_dir'])
        
        return results
        
    except Exception as e:
        print(f"❌ 基准测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_multi_scenario_benchmark():
    """运行多场景基准测试"""
    scenarios = ['testing', 'light_load', 'heavy_load', 'performance']
    
    print("🔬 多场景基准测试")
    print("=" * 60)
    
    all_results = {}
    
    for scenario in scenarios:
        print(f"\n📋 场景: {scenario}")
        print("-" * 40)
        
        try:
            results = run_single_scenario_benchmark(scenario)
            if results:
                all_results[scenario] = results
                
                # 显示该场景的简要结果
                for algo_name, data in results.items():
                    if 'error' not in data:
                        metrics = data['metrics']
                        print(f"   {algo_name}: 成功率={metrics.get('success_rate', 0):.1%}, "
                              f"延迟={metrics.get('avg_path_delay', 0):.3f}ms")
                    else:
                        print(f"   {algo_name}: 失败")
            
        except Exception as e:
            print(f"   ❌ 场景 {scenario} 失败: {e}")
    
    # 生成综合对比
    if all_results:
        print("\n📊 多场景综合对比:")
        print("=" * 80)
        generate_multi_scenario_summary(all_results)
    
    return all_results


def generate_multi_scenario_summary(all_results: dict):
    """生成多场景综合对比"""
    algorithms = ['LDMR', 'SPF', 'ECMP']
    scenarios = list(all_results.keys())
    
    print(f"{'场景':<12} {'算法':<8} {'成功率':<8} {'平均延迟(ms)':<12} {'执行时间(s)':<12}")
    print("-" * 60)
    
    for scenario in scenarios:
        results = all_results[scenario]
        for algo in algorithms:
            if algo in results and 'error' not in results[algo]:
                metrics = results[algo]['metrics']
                success_rate = metrics.get('success_rate', 0)
                avg_delay = metrics.get('avg_path_delay', 0)
                exec_time = metrics.get('execution_time', 0)
                
                print(f"{scenario:<12} {algo:<8} {success_rate:<8.1%} "
                      f"{avg_delay:<12.3f} {exec_time:<12.2f}")
            else:
                print(f"{scenario:<12} {algo:<8} {'ERROR':<8} {'N/A':<12} {'N/A':<12}")


def run_algorithm_comparison():
    """运行算法详细对比"""
    print("🔬 算法详细对比分析")
    print("=" * 60)
    
    # 使用performance场景进行详细对比
    config = load_scenario_config('performance')
    
    # 构建网络
    network_config = config['network']
    builder = LEONetworkBuilder(
        network_config['constellation'], 
        network_config['ground_stations']
    )
    topology = builder.build_network()
    
    # 生成流量
    traffic_config = config['traffic']
    generator = TrafficGenerator()
    ground_stations = [
        node.id for node in topology.nodes.values()
        if node.type.value == 'ground_station'
    ]
    
    demands = generator.generate_traffic_demands(
        ground_station_ids=ground_stations,
        total_traffic=traffic_config['total_gbps'],
        duration=traffic_config['duration']
    )
    
    # 运行基准测试
    manager = BenchmarkManager()
    results = manager.run_benchmark(topology, demands)
    
    # 生成详细报告
    print("\n📋 详细性能报告:")
    print(manager.generate_detailed_report(results))
    
    return results


def interactive_benchmark():
    """交互式基准测试"""
    while True:
        print("\n" + "="*50)
        print("🔬 基准测试工具")
        print("="*50)
        print("1. 🧪 单场景基准测试")
        print("2. 📊 多场景基准测试")
        print("3. 📋 算法详细对比")
        print("4. 🔄 自定义测试")
        print("5. ❌ 退出")
        print("="*50)
        
        choice = input("请选择操作 (1-5): ").strip()
        
        if choice == '1':
            scenarios = ['testing', 'light_load', 'heavy_load', 'performance']
            print("\n可用场景:")
            for i, scenario in enumerate(scenarios, 1):
                print(f"  {i}. {scenario}")
            
            try:
                idx = int(input("请选择场景 (1-4): ")) - 1
                if 0 <= idx < len(scenarios):
                    run_single_scenario_benchmark(scenarios[idx])
                else:
                    print("❌ 无效选择")
            except ValueError:
                print("❌ 请输入有效数字")
                
        elif choice == '2':
            run_multi_scenario_benchmark()
            
        elif choice == '3':
            run_algorithm_comparison()
            
        elif choice == '4':
            print("📝 自定义测试配置:")
            scenario = input("场景名称 [performance]: ").strip() or 'performance'
            run_single_scenario_benchmark(scenario)
            
        elif choice == '5':
            print("👋 退出")
            break
            
        else:
            print("❌ 无效选项")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'single':
            scenario = sys.argv[2] if len(sys.argv) > 2 else 'testing'
            run_single_scenario_benchmark(scenario)
            
        elif command == 'multi':
            run_multi_scenario_benchmark()
            
        elif command == 'compare':
            run_algorithm_comparison()
            
        elif command == 'interactive':
            interactive_benchmark()
            
        else:
            print(f"❌ 未知命令: {command}")
            print("支持的命令:")
            print("  single [scenario]  - 单场景基准测试")
            print("  multi             - 多场景基准测试") 
            print("  compare           - 算法详细对比")
            print("  interactive       - 交互式模式")
    else:
        interactive_benchmark()


if __name__ == "__main__":
    main()
