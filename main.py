#!/usr/bin/env python3
"""
LDMR算法主程序
4个核心功能：运行LDMR、基准对比、参数分析、切换场景
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from config import load_config, list_scenarios
from benchmark import SimpleBenchmark
from param_analysis import ParameterAnalysis
from output.result_exporter import export_all_results
from output.visualizer import generate_all_visualizations

# 简单的LDMR运行功能
def run_ldmr_only():
    """只运行LDMR算法"""
    print("🚀 运行LDMR算法")
    print("=" * 40)

    try:
        from topology.satellite_constellation import LEONetworkBuilder
        from traffic.traffic_model import TrafficGenerator
        from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig

        # 加载配置
        config = load_config()

        # 创建网络
        print("🔧 构建网络...")
        builder = LEONetworkBuilder(
            config['network']['constellation'],
            config['network']['ground_stations']
        )
        topology = builder.build_network()

        # 生成流量
        print("📈 生成流量...")
        generator = TrafficGenerator()
        ground_stations = [
            node.id for node in topology.nodes.values()
            if node.type.value == 'ground_station'
        ]
        demands = generator.generate_traffic_demands(
            ground_station_ids=ground_stations,
            total_traffic=config['traffic']['total_gbps'],
            duration=config['traffic']['duration']
        )

        # 运行LDMR
        print("⚡ 运行LDMR算法...")
        ldmr_config = LDMRConfig(
            K=config['algorithm']['K'],
            r1=config['algorithm']['r1'],
            r2=config['algorithm']['r2'],
            r3=config['algorithm']['r3'],
            Ne_th=config['algorithm']['Ne_th']
        )

        ldmr = LDMRAlgorithm(ldmr_config)
        results = ldmr.run_ldmr_algorithm(topology, demands)

        # 显示结果
        stats = ldmr.get_algorithm_statistics(results)
        disjoint_stats = ldmr.verify_path_disjointness(results)

        print("\n📊 LDMR运行结果:")
        print(f"   成功率: {stats.get('success_rate', 0):.1%}")
        print(f"   平均延迟: {stats.get('avg_path_delay', 0) * 1000:.2f}ms")
        print(f"   总路径数: {stats.get('total_paths_calculated', 0)}")
        print(f"   平均路径数: {stats.get('avg_paths_per_demand', 0):.1f}")
        print(f"   路径不相交率: {disjoint_stats.get('disjoint_rate', 0):.1%}")
        print(f"   执行时间: {stats.get('total_computation_time', 0):.2f}s")

        print("✅ LDMR算法运行完成!")

        # 导出结果和生成图表
        print("\n📊 导出结果和生成图表...")
        try:
            # 导出结果数据
            output_files = export_all_results(
                ldmr_results=results,
                config=config
            )

            # 生成可视化图表
            chart_files = generate_all_visualizations(
                ldmr_results=results
            )

            print("✅ 结果导出和可视化完成!")
            print("📁 查看输出文件:")
            print(f"   数据文件: {output_files.get('ldmr_csv', 'N/A')}")
            print(f"   摘要报告: {output_files.get('summary_txt', 'N/A')}")
            print(f"   路径分析图: {chart_files.get('path_analysis', 'N/A')}")
            print(f"   性能趋势图: {chart_files.get('performance_trends', 'N/A')}")

        except Exception as e:
            print(f"⚠️  输出生成失败: {e}")

    except Exception as e:
        print(f"❌ LDMR运行失败: {e}")


def run_benchmark():
    """运行基准对比"""
    print("📊 基准算法对比")
    print("=" * 40)

    try:
        config = load_config()
        benchmark = SimpleBenchmark(config)
        benchmark.run_benchmark()

    except Exception as e:
        print(f"❌ 基准测试失败: {e}")


def run_param_analysis():
    """运行参数分析"""
    print("🔬 参数敏感性分析")
    print("=" * 40)

    try:
        config = load_config()
        analyzer = ParameterAnalysis(config)
        analyzer.run_full_analysis()

    except Exception as e:
        print(f"❌ 参数分析失败: {e}")


def switch_scenario():
    """切换场景"""
    print("🔄 切换场景")
    print("=" * 40)

    try:
        scenarios = list_scenarios()

        if not scenarios:
            print("❌ 没有找到可用场景")
            return

        print("可用场景:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"  {i}. {scenario}")

        choice = input("\n请选择场景 (输入编号): ").strip()

        try:
            scenario_idx = int(choice) - 1
            if 0 <= scenario_idx < len(scenarios):
                scenario_name = scenarios[scenario_idx]

                # 加载并显示场景配置
                config = load_config(scenario_name)
                print(f"\n✅ 已切换到场景: {scenario_name}")
                print("场景配置:")
                print(f"   星座类型: {config['network']['constellation']}")
                print(f"   地面站数: {config['network']['ground_stations']}")
                print(f"   总流量: {config['traffic']['total_gbps']} Gbps")
                print(f"   算法K值: {config['algorithm']['K']}")
                print(f"   算法r3值: {config['algorithm']['r3']}")

                # 询问是否运行
                run_now = input("\n是否立即运行LDMR? (y/n): ").strip().lower()
                if run_now == 'y':
                    # 临时使用新配置运行LDMR
                    run_ldmr_with_config(config)

            else:
                print("❌ 无效选择")

        except ValueError:
            print("❌ 请输入有效数字")

    except Exception as e:
        print(f"❌ 场景切换失败: {e}")


def run_ldmr_with_config(config):
    """使用指定配置运行LDMR"""
    try:
        from topology.satellite_constellation import LEONetworkBuilder
        from traffic.traffic_model import TrafficGenerator
        from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig

        print("\n🚀 使用新场景运行LDMR...")

        # 创建网络
        builder = LEONetworkBuilder(
            config['network']['constellation'],
            config['network']['ground_stations']
        )
        topology = builder.build_network()

        # 生成流量
        generator = TrafficGenerator()
        ground_stations = [
            node.id for node in topology.nodes.values()
            if node.type.value == 'ground_station'
        ]
        demands = generator.generate_traffic_demands(
            ground_station_ids=ground_stations,
            total_traffic=config['traffic']['total_gbps'],
            duration=config['traffic']['duration']
        )

        # 运行LDMR
        ldmr_config = LDMRConfig(
            K=config['algorithm']['K'],
            r1=config['algorithm']['r1'],
            r2=config['algorithm']['r2'],
            r3=config['algorithm']['r3'],
            Ne_th=config['algorithm']['Ne_th']
        )

        ldmr = LDMRAlgorithm(ldmr_config)
        results = ldmr.run_ldmr_algorithm(topology, demands)

        # 显示结果
        stats = ldmr.get_algorithm_statistics(results)
        print(f"\n📊 结果: 成功率={stats.get('success_rate', 0):.1%}, "
              f"延迟={stats.get('avg_path_delay', 0) * 1000:.2f}ms")

        # 快速导出结果
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 只导出摘要报告
            from output.result_exporter import ResultExporter
            exporter = ResultExporter()
            summary_path = exporter.generate_summary_report(
                ldmr_results=results,
                config=config,
                timestamp=timestamp
            )

            print(f"📝 详细报告: {summary_path}")

        except Exception as e:
            print(f"⚠️  报告生成失败: {e}")


    except Exception as e:
        print(f"❌ 运行失败: {e}")


def show_menu():
    """显示主菜单"""
    print("\n" + "=" * 50)
    print("🎯 LDMR算法仿真系统")
    print("=" * 50)
    print("1. 🚀 运行LDMR算法")
    print("2. 📊 基准算法对比 (LDMR vs SPF vs ECMP)")
    print("3. 🔬 参数敏感性分析")
    print("4. 🔄 切换场景配置")
    print("5. ❌ 退出")
    print("=" * 50)

    return input("请选择功能 (1-5): ").strip()


def main():
    """主函数"""
    print("🎯 LDMR算法简化仿真系统")
    print("   核心功能: LDMR算法、基准对比、参数分析、场景切换")

    while True:
        try:
            choice = show_menu()

            if choice == '1':
                run_ldmr_only()

            elif choice == '2':
                run_benchmark()

            elif choice == '3':
                run_param_analysis()

            elif choice == '4':
                switch_scenario()

            elif choice == '5':
                print("\n👋 退出程序")
                break

            else:
                print("❌ 无效选择，请重新输入")

            input("\n按回车键继续...")

        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 程序错误: {e}")
            input("按回车键继续...")


if __name__ == "__main__":
    main()