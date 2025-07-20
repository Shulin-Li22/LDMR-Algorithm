#!/usr/bin/env python3
"""
LDMR参数敏感性分析
测试关键参数对性能的影响
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from config import load_config
from topology.satellite_constellation import LEONetworkBuilder
from traffic.traffic_model import TrafficGenerator
from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig
from output.result_exporter import export_parameter_analysis
from output.visualizer import plot_parameter_sensitivity


class ParameterAnalysis:
    def __init__(self, base_config):
        self.base_config = base_config

    def create_test_setup(self):
        """创建测试环境（小规模，快速测试）"""
        print("🔧 创建测试环境...")

        # 使用较小规模以加快测试
        builder = LEONetworkBuilder('globalstar', 8)
        topology = builder.build_network()

        generator = TrafficGenerator()
        ground_stations = [
            node.id for node in topology.nodes.values()
            if node.type.value == 'ground_station'
        ]

        demands = generator.generate_traffic_demands(
            ground_station_ids=ground_stations,
            total_traffic=4.0,  # 较小流量
            duration=120.0  # 较短时间
        )

        print(f"   测试网络: {len(topology.nodes)}节点, {len(topology.links)}链路")
        print(f"   测试流量: {len(demands)}个需求")

        return topology, demands

    def test_single_parameter(self, topology, demands, param_name, param_values):
        """测试单个参数的影响"""
        print(f"\n🔬 测试参数: {param_name}")
        print(f"   测试值: {param_values}")

        results = {}

        for value in param_values:
            print(f"   测试 {param_name}={value}...")

            # 创建配置
            config = LDMRConfig(
                K=self.base_config['algorithm']['K'],
                r1=self.base_config['algorithm']['r1'],
                r2=self.base_config['algorithm']['r2'],
                r3=self.base_config['algorithm']['r3'],
                Ne_th=self.base_config['algorithm']['Ne_th'],
                enable_statistics=True
            )

            # 修改测试参数
            if param_name == 'r3':
                config.r3 = value
            elif param_name == 'K':
                config.K = value
            elif param_name == 'Ne_th':
                config.Ne_th = value
            elif param_name == 'r2':
                config.r2 = value

            try:
                # 运行LDMR
                ldmr = LDMRAlgorithm(config)
                start_time = time.time()
                ldmr_results = ldmr.run_ldmr_algorithm(topology, demands)
                exec_time = time.time() - start_time

                # 计算指标
                stats = ldmr.get_algorithm_statistics(ldmr_results)
                disjoint_stats = ldmr.verify_path_disjointness(ldmr_results)

                results[value] = {
                    'success_rate': stats.get('success_rate', 0),
                    'avg_delay': stats.get('avg_path_delay', 0) * 1000,
                    'total_paths': stats.get('total_paths_calculated', 0),
                    'avg_computation_time': stats.get('avg_computation_time', 0),
                    'execution_time': exec_time,
                    'disjoint_rate': disjoint_stats.get('disjoint_rate', 0)
                }

                print(f"     成功率: {results[value]['success_rate']:.1%}, "
                      f"延迟: {results[value]['avg_delay']:.2f}ms")

            except Exception as e:
                print(f"     ❌ 失败: {e}")
                results[value] = {'error': str(e)}

        return results

    def analyze_r3_parameter(self, topology, demands):
        """分析r3参数（权重上界）"""
        print("\n📊 分析r3参数（权重上界）")
        print("   r3控制高使用频次链路的权重范围")

        # 测试不同r3值
        r3_values = [20, 30, 40, 50, 60, 70]
        results = self.test_single_parameter(topology, demands, 'r3', r3_values)

        return self.find_best_parameter('r3', results)

    def analyze_K_parameter(self, topology, demands):
        """分析K参数（路径数量）"""
        print("\n📊 分析K参数（路径数量）")
        print("   K控制每个节点对计算的路径数量")

        # 测试不同K值
        K_values = [2, 3, 4]
        results = self.test_single_parameter(topology, demands, 'K', K_values)

        return self.find_best_parameter('K', results)

    def analyze_Ne_th_parameter(self, topology, demands):
        """分析Ne_th参数（利用频次阈值）"""
        print("\n📊 分析Ne_th参数（利用频次阈值）")
        print("   Ne_th控制权重更新的触发阈值")

        # 测试不同Ne_th值
        Ne_th_values = [1, 2, 3, 4]
        results = self.test_single_parameter(topology, demands, 'Ne_th', Ne_th_values)

        return self.find_best_parameter('Ne_th', results)

    def find_best_parameter(self, param_name, results):
        """找到最优参数值"""
        valid_results = {k: v for k, v in results.items() if 'error' not in v}

        if not valid_results:
            print(f"   ❌ {param_name}参数测试全部失败")
            return None

        # 按成功率排序，成功率相同时按延迟排序
        best_value = max(valid_results.keys(),
                         key=lambda x: (valid_results[x]['success_rate'],
                                        -valid_results[x]['avg_delay']))

        best_result = valid_results[best_value]
        print(f"\n🎯 最优{param_name}值: {best_value}")
        print(f"   成功率: {best_result['success_rate']:.1%}")
        print(f"   平均延迟: {best_result['avg_delay']:.2f}ms")
        print(f"   路径不相交率: {best_result['disjoint_rate']:.1%}")

        return best_value, best_result

    def display_parameter_summary(self, param_results):
        """显示参数分析总结"""
        print("\n" + "=" * 60)
        print("📋 参数敏感性分析总结")
        print("=" * 60)

        for param_name, (best_value, best_result) in param_results.items():
            if best_value is not None:
                print(f"{param_name}最优值: {best_value}")
                print(f"  - 成功率: {best_result['success_rate']:.1%}")
                print(f"  - 平均延迟: {best_result['avg_delay']:.2f}ms")
                print(f"  - 执行时间: {best_result['execution_time']:.2f}s")
                print()

        print("💡 参数调优建议:")
        print("  1. r3=50 通常是最优选择（论文验证）")
        print("  2. K=2 在性能和复杂度间取得平衡")
        print("  3. Ne_th=2 适合大多数场景")
        print("  4. 高负载场景可考虑增大Ne_th值")
        print("=" * 60)

    def run_full_analysis(self):
        """运行完整参数分析"""
        print("🚀 LDMR参数敏感性分析")
        print("=" * 60)

        # 创建测试环境
        topology, demands = self.create_test_setup()

        # 分析各个参数
        param_results = {}

        try:
            param_results['r3'] = self.analyze_r3_parameter(topology, demands)
        except Exception as e:
            print(f"❌ r3参数分析失败: {e}")
            param_results['r3'] = (None, None)

        try:
            param_results['K'] = self.analyze_K_parameter(topology, demands)
        except Exception as e:
            print(f"❌ K参数分析失败: {e}")
            param_results['K'] = (None, None)

        try:
            param_results['Ne_th'] = self.analyze_Ne_th_parameter(topology, demands)
        except Exception as e:
            print(f"❌ Ne_th参数分析失败: {e}")
            param_results['Ne_th'] = (None, None)

        # 显示总结
        self.display_parameter_summary(param_results)

        # 导出结果
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 导出参数分析数据
            csv_path = export_parameter_analysis(param_results, timestamp)

            # 生成敏感性图表
            chart_path = plot_parameter_sensitivity(param_results, timestamp)

            print(f"\n📊 参数分析结果已保存:")
            print(f"   数据文件: {csv_path}")
            print(f"   图表文件: {chart_path}")

        except Exception as e:
            print(f"⚠️  结果导出失败: {e}")

        return param_results


def main():
    """主函数"""
    print("🎯 LDMR参数敏感性分析工具")

    # 加载基础配置
    config = load_config()

    # 运行参数分析
    analyzer = ParameterAnalysis(config)
    results = analyzer.run_full_analysis()

    print("\n✅ 参数分析完成!")


if __name__ == "__main__":
    main()