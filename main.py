#!/usr/bin/env python3
"""
LDMR算法主运行脚本
提供统一的入口点和交互式界面
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 确保输出目录存在
results_dir = os.path.join(current_dir, 'results')
os.makedirs(results_dir, exist_ok=True)
os.makedirs(os.path.join(results_dir, 'figures'), exist_ok=True)
os.makedirs(os.path.join(results_dir, 'data'), exist_ok=True)
os.makedirs(os.path.join(results_dir, 'logs'), exist_ok=True)


class LDMRRunner:
    """LDMR算法运行器"""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        self.start_time = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log_message(self, message: str, level: str = "INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)

        # 保存到日志文件
        log_file = os.path.join(self.output_dir, 'logs', f'ldmr_run_{self.session_id}.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    def show_banner(self):
        """显示程序横幅"""
        banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       LDMR 算法仿真系统 v1.0                                  ║
║                                                                              ║
║   Link Disjoint Multipath Routing for LEO Satellite Networks                ║
║   基于论文: "A GNN-Enabled Multipath Routing Algorithm for                   ║
║            Spatial-Temporal Varying LEO Satellite Networks"                 ║
║                                                                              ║
║   会话ID: {self.session_id}                                        ║
║   输出目录: {self.output_dir:<50} ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        self.log_message("LDMR仿真系统启动")

    def run_environment_test(self) -> bool:
        """运行环境测试"""
        self.log_message("开始环境测试")

        try:
            # 测试基本导入
            from topology.satellite_constellation import LEONetworkBuilder
            from traffic.traffic_model import TrafficGenerator
            from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig
            from algorithms.basic_algorithms import DijkstraPathFinder

            self.log_message("所有核心模块导入成功")

            # 创建简单测试
            builder = LEONetworkBuilder('globalstar', 5)
            topology = builder.build_network()

            stats = topology.get_statistics()
            self.log_message(f"测试网络创建成功: {stats}")

            # 测试流量生成
            generator = TrafficGenerator()
            gs_list = [node.id for node in topology.nodes.values()
                       if node.type.value == 'ground_station']

            demands = generator.generate_traffic_demands(
                ground_station_ids=gs_list,
                total_traffic=2.0,
                duration=60.0
            )

            self.log_message(f"测试流量生成成功: {len(demands)} 个需求")

            # 测试LDMR算法
            config = LDMRConfig(K=2, r3=50)
            ldmr = LDMRAlgorithm(config)

            # 只测试少量需求
            test_demands = demands[:5]
            results = ldmr.run_ldmr_algorithm(topology, test_demands)

            success_count = len([r for r in results if r.success])
            self.log_message(f"LDMR算法测试成功: {success_count}/{len(test_demands)} 成功")

            self.log_message("环境测试完成 - 所有组件正常工作", "SUCCESS")
            return True

        except Exception as e:
            self.log_message(f"环境测试失败: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def run_basic_ldmr_simulation(self, constellation: str = 'globalstar',
                                  num_ground_stations: int = 10,
                                  total_traffic: float = 6.0,
                                  duration: float = 180.0,
                                  scenario: str = 'performance') -> Dict:
        """运行基础LDMR仿真"""

        self.log_message(f"开始基础LDMR仿真")
        self.log_message(f"参数: {constellation}, {num_ground_stations}个地面站, {total_traffic}Gbps, {duration}s")

        sim_start_time = time.time()

        try:
            # 导入必要模块
            from topology.satellite_constellation import LEONetworkBuilder
            from traffic.traffic_model import TrafficGenerator
            from algorithms.ldmr_algorithms import run_ldmr_simulation, create_ldmr_config_for_scenario

            # 1. 构建网络拓扑
            self.log_message("构建网络拓扑...")
            builder = LEONetworkBuilder(constellation, num_ground_stations)
            topology = builder.build_network()

            network_stats = topology.get_statistics()
            self.log_message(f"网络构建完成: {network_stats}")

            # 2. 生成流量需求
            self.log_message("生成流量需求...")
            generator = TrafficGenerator()
            gs_list = [node.id for node in topology.nodes.values()
                       if node.type.value == 'ground_station']

            demands = generator.generate_traffic_demands(
                ground_station_ids=gs_list,
                total_traffic=total_traffic,
                duration=duration
            )

            traffic_stats = generator.get_flow_statistics(demands)
            self.log_message(f"流量生成完成: {traffic_stats}")

            # 3. 运行LDMR算法
            self.log_message("运行LDMR算法...")
            config = create_ldmr_config_for_scenario(scenario)

            ldmr_results, ldmr_statistics = run_ldmr_simulation(
                topology=topology,
                traffic_demands=demands,
                config=config,
                scenario=scenario
            )

            # 4. 验证路径不相交性
            self.log_message("验证路径不相交性...")
            from algorithms.ldmr_algorithms import LDMRAlgorithm

            ldmr_alg = LDMRAlgorithm(config)
            disjoint_stats = ldmr_alg.verify_path_disjointness(ldmr_results)

            # 5. 整理结果
            simulation_time = time.time() - sim_start_time

            results = {
                'session_id': self.session_id,
                'simulation_params': {
                    'constellation': constellation,
                    'num_ground_stations': num_ground_stations,
                    'total_traffic': total_traffic,
                    'duration': duration,
                    'scenario': scenario
                },
                'network_stats': network_stats,
                'traffic_stats': traffic_stats,
                'ldmr_statistics': ldmr_statistics,
                'disjoint_verification': disjoint_stats,
                'simulation_time': simulation_time,
                'timestamp': datetime.now().isoformat()
            }

            self.log_message(f"仿真完成 (耗时: {simulation_time:.2f}s)")
            self.log_message(f"LDMR性能: 成功率={ldmr_statistics.get('success_rate', 0):.2%}, "
                             f"平均延迟={ldmr_statistics.get('avg_path_delay', 0):.2f}ms")

            return results

        except Exception as e:
            self.log_message(f"仿真失败: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    def run_parameter_analysis(self, parameter: str = 'r3',
                               values: List = None) -> Dict:
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

        self.log_message(f"开始参数敏感性分析: {parameter} = {values}")

        try:
            from topology.satellite_constellation import LEONetworkBuilder
            from traffic.traffic_model import TrafficGenerator
            from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig

            results = {}

            for value in values:
                self.log_message(f"测试 {parameter} = {value}")

                # 创建配置
                if parameter == 'r3':
                    config = LDMRConfig(K=2, r1=1, r2=10, r3=value, Ne_th=2)
                elif parameter == 'K':
                    config = LDMRConfig(K=value, r1=1, r2=10, r3=50, Ne_th=2)
                elif parameter == 'Ne_th':
                    config = LDMRConfig(K=2, r1=1, r2=10, r3=50, Ne_th=value)
                else:
                    config = LDMRConfig()

                # 构建网络
                builder = LEONetworkBuilder('globalstar', 8)
                topology = builder.build_network()

                # 生成流量
                generator = TrafficGenerator()
                gs_list = [node.id for node in topology.nodes.values()
                           if node.type.value == 'ground_station']

                demands = generator.generate_traffic_demands(
                    ground_station_ids=gs_list,
                    total_traffic=4.0,
                    duration=120.0
                )

                # 运行LDMR
                ldmr = LDMRAlgorithm(config)
                ldmr_results = ldmr.run_ldmr_algorithm(topology, demands)
                stats = ldmr.get_algorithm_statistics(ldmr_results)

                results[value] = {
                    'success_rate': stats.get('success_rate', 0),
                    'avg_path_delay': stats.get('avg_path_delay', 0),
                    'total_paths': stats.get('total_paths_calculated', 0),
                    'avg_computation_time': stats.get('avg_computation_time', 0)
                }

                self.log_message(f"  结果: 成功率={results[value]['success_rate']:.2%}, "
                                 f"延迟={results[value]['avg_path_delay']:.2f}ms")

            # 找到最优参数
            best_value = max(results.keys(), key=lambda x: results[x]['success_rate'])
            self.log_message(f"最优参数: {parameter} = {best_value} "
                             f"(成功率: {results[best_value]['success_rate']:.2%})")

            return {
                'parameter': parameter,
                'values': values,
                'results': results,
                'best_value': best_value,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.log_message(f"参数分析失败: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    def run_multi_scenario_evaluation(self) -> Dict:
        """运行多场景评估"""

        self.log_message("开始多场景评估")

        scenarios = [
            ('testing', 'globalstar', 8, 3.0),
            ('light_load', 'globalstar', 10, 4.0),
            ('heavy_load', 'globalstar', 12, 8.0),
            ('performance', 'iridium', 10, 6.0)
        ]

        all_results = {}

        for scenario_name, constellation, num_gs, traffic in scenarios:
            self.log_message(f"运行场景: {scenario_name}")

            try:
                result = self.run_basic_ldmr_simulation(
                    constellation=constellation,
                    num_ground_stations=num_gs,
                    total_traffic=traffic,
                    duration=150.0,
                    scenario=scenario_name
                )

                all_results[scenario_name] = result

                if 'error' not in result:
                    stats = result['ldmr_statistics']
                    self.log_message(f"场景 {scenario_name} 完成: "
                                     f"成功率={stats.get('success_rate', 0):.2%}")
                else:
                    self.log_message(f"场景 {scenario_name} 失败: {result['error']}", "ERROR")

            except Exception as e:
                self.log_message(f"场景 {scenario_name} 异常: {e}", "ERROR")
                all_results[scenario_name] = {'error': str(e)}

        self.log_message("多场景评估完成")

        return {
            'evaluation_type': 'multi_scenario',
            'scenarios': scenarios,
            'results': all_results,
            'timestamp': datetime.now().isoformat()
        }

    def save_results(self, results: Dict, filename: str = None):
        if filename is None:
            filename = f"ldmr_results_{self.session_id}.json"

        filepath = os.path.join(self.output_dir, 'data', filename)

        try:
            # 清理不能序列化的数据
            clean_results = self._clean_results_for_json(results)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(clean_results, f, indent=2, ensure_ascii=False, default=str)

            self.log_message(f"结果已保存到: {filepath}")

        except Exception as e:
            self.log_message(f"保存结果失败: {e}", "ERROR")

    def _clean_results_for_json(self, data):
        """清理数据以便JSON序列化"""
        if isinstance(data, dict):
            return {str(k): self._clean_results_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_results_for_json(item) for item in data]
        elif isinstance(data, tuple):
            return list(data)
        elif hasattr(data, '__dict__'):
            return str(data)
        else:
            return data

    def generate_summary_report(self, results: Dict) -> str:
        """生成摘要报告"""

        report = f"""
LDMR算法仿真摘要报告
==================

会话ID: {self.session_id}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总运行时间: {time.time() - self.start_time:.2f} 秒

"""

        if 'simulation_params' in results:
            params = results['simulation_params']
            report += f"""
仿真参数:
- 星座类型: {params['constellation']}
- 地面站数: {params['num_ground_stations']}
- 总流量: {params['total_traffic']} Gbps
- 仿真时长: {params['duration']} 秒
- 场景: {params['scenario']}

"""

        if 'network_stats' in results:
            net_stats = results['network_stats']
            report += f"""
网络统计:
- 卫星数: {net_stats.get('satellites', 0)}
- 地面站数: {net_stats.get('ground_stations', 0)}
- 链路数: {net_stats.get('total_links', 0)}
- 网络连通性: {'是' if net_stats.get('is_connected', False) else '否'}

"""

        if 'ldmr_statistics' in results:
            ldmr_stats = results['ldmr_statistics']
            report += f"""
LDMR算法性能:
- 成功率: {ldmr_stats.get('success_rate', 0):.2%}
- 平均路径延迟: {ldmr_stats.get('avg_path_delay', 0):.2f} ms
- 总路径数: {ldmr_stats.get('total_paths_calculated', 0)}
- 平均计算时间: {ldmr_stats.get('avg_computation_time', 0):.3f} s

"""

        if 'disjoint_verification' in results:
            disjoint = results['disjoint_verification']
            report += f"""
路径不相交性验证:
- 不相交路径数: {disjoint.get('disjoint_results', 0)}
- 冲突路径数: {disjoint.get('non_disjoint_results', 0)}
- 不相交率: {disjoint.get('disjoint_rate', 0):.2%}

"""

        report += "=" * 50

        return report

    def show_interactive_menu(self):
        """显示交互式菜单"""

        menu = """
🎯 请选择操作:

1. 🧪 环境测试           - 验证所有组件正常工作
2. 🚀 基础LDMR仿真       - 运行标准LDMR算法
3. 📊 多场景评估         - 测试不同场景下的性能
4. 🔬 参数敏感性分析     - 分析关键参数影响
5. 📋 查看历史结果       - 浏览之前的仿真结果
6. 🌐 自定义仿真         - 使用自定义参数
7. ❌ 退出

请输入选项编号 (1-7): """

        return input(menu).strip()

    def run_interactive_mode(self):
        """运行交互式模式"""

        while True:
            try:
                choice = self.show_interactive_menu()

                if choice == '1':
                    success = self.run_environment_test()
                    if not success:
                        print("❌ 环境测试失败，请检查依赖")

                elif choice == '2':
                    results = self.run_basic_ldmr_simulation()
                    if 'error' not in results:
                        report = self.generate_summary_report(results)
                        print(report)
                        self.save_results(results)

                elif choice == '3':
                    results = self.run_multi_scenario_evaluation()
                    print(f"✅ 多场景评估完成，共 {len(results['results'])} 个场景")
                    self.save_results(results, f"multi_scenario_{self.session_id}.json")

                elif choice == '4':
                    param = input("请输入参数名 (r3/K/Ne_th) [r3]: ").strip() or 'r3'
                    results = self.run_parameter_analysis(param)
                    if 'error' not in results:
                        print(f"✅ 参数分析完成，最优值: {results['best_value']}")
                        self.save_results(results, f"param_analysis_{param}_{self.session_id}.json")

                elif choice == '5':
                    data_dir = os.path.join(self.output_dir, 'data')
                    if os.path.exists(data_dir):
                        files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
                        if files:
                            print(f"📁 找到 {len(files)} 个结果文件:")
                            for i, file in enumerate(files[-10:], 1):  # 显示最近10个
                                print(f"  {i}. {file}")
                        else:
                            print("❌ 没有找到历史结果文件")
                    else:
                        print("❌ 结果目录不存在")

                elif choice == '6':
                    print("🌐 自定义仿真参数:")
                    constellation = input("星座类型 (globalstar/iridium) [globalstar]: ").strip() or 'globalstar'
                    num_gs = int(input("地面站数量 [10]: ").strip() or '10')
                    traffic = float(input("总流量 (Gbps) [6.0]: ").strip() or '6.0')
                    duration = float(input("仿真时长 (秒) [180]: ").strip() or '180')

                    results = self.run_basic_ldmr_simulation(
                        constellation=constellation,
                        num_ground_stations=num_gs,
                        total_traffic=traffic,
                        duration=duration
                    )

                    if 'error' not in results:
                        report = self.generate_summary_report(results)
                        print(report)
                        self.save_results(results)

                elif choice == '7':
                    self.log_message("用户退出程序")
                    print("\n👋 感谢使用LDMR算法仿真系统！")
                    break

                else:
                    print("❌ 无效选项，请重新选择")

                input("\n按回车键继续...")

            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断")
                break
            except Exception as e:
                self.log_message(f"交互模式错误: {e}", "ERROR")
                print(f"❌ 发生错误: {e}")


def parse_arguments():
    """解析命令行参数"""

    parser = argparse.ArgumentParser(
        description='LDMR算法仿真系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                          # 交互式模式
  python main.py --test                   # 环境测试
  python main.py --run                    # 基础仿真
  python main.py --multi-scenario         # 多场景评估
  python main.py --param-analysis r3      # 参数分析
  python main.py --custom --constellation iridium --traffic 8.0
        """
    )

    # 运行模式
    parser.add_argument('--test', action='store_true', help='运行环境测试')
    parser.add_argument('--run', action='store_true', help='运行基础LDMR仿真')
    parser.add_argument('--multi-scenario', action='store_true', help='运行多场景评估')
    parser.add_argument('--param-analysis', choices=['r3', 'K', 'Ne_th'], help='参数敏感性分析')
    parser.add_argument('--custom', action='store_true', help='自定义仿真')

    # 仿真参数
    parser.add_argument('--constellation', choices=['globalstar', 'iridium'],
                        default='globalstar', help='星座类型')
    parser.add_argument('--ground-stations', type=int, default=10, help='地面站数量')
    parser.add_argument('--traffic', type=float, default=6.0, help='总流量 (Gbps)')
    parser.add_argument('--duration', type=float, default=180.0, help='仿真时长 (秒)')
    parser.add_argument('--scenario', choices=['testing', 'light_load', 'heavy_load', 'performance'],
                        default='performance', help='仿真场景')

    # 输出选项
    parser.add_argument('--output', default='results', help='输出目录')
    parser.add_argument('--quiet', action='store_true', help='减少输出信息')

    return parser.parse_args()


def main():
    """主函数"""

    args = parse_arguments()

    # 创建运行器
    runner = LDMRRunner(args.output)

    # 显示横幅
    if not args.quiet:
        runner.show_banner()

    try:
        # 根据参数选择运行模式
        if args.test:
            runner.run_environment_test()

        elif args.run:
            results = runner.run_basic_ldmr_simulation(
                constellation=args.constellation,
                num_ground_stations=args.ground_stations,
                total_traffic=args.traffic,
                duration=args.duration,
                scenario=args.scenario
            )

            if 'error' not in results:
                report = runner.generate_summary_report(results)
                print(report)
                runner.save_results(results)

        elif args.multi_scenario:
            results = runner.run_multi_scenario_evaluation()
            runner.save_results(results, f"multi_scenario_{runner.session_id}.json")

        elif args.param_analysis:
            results = runner.run_parameter_analysis(args.param_analysis)
            if 'error' not in results:
                runner.save_results(results, f"param_analysis_{args.param_analysis}_{runner.session_id}.json")

        elif args.custom:
            results = runner.run_basic_ldmr_simulation(
                constellation=args.constellation,
                num_ground_stations=args.ground_stations,
                total_traffic=args.traffic,
                duration=args.duration,
                scenario=args.scenario
            )

            if 'error' not in results:
                report = runner.generate_summary_report(results)
                print(report)
                runner.save_results(results)

        else:
            # 默认交互式模式
            runner.run_interactive_mode()

    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        runner.log_message(f"程序异常: {e}", "ERROR")
        print(f"❌ 程序发生异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner.log_message("程序结束")


if __name__ == "__main__":
    main()