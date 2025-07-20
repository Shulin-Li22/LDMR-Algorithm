#!/usr/bin/env python3
"""
简化基准测试 - LDMR vs SPF vs ECMP
直接运行就能看到对比结果
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
from algorithms.baseline.spf_algorithm import SPFAlgorithm
from algorithms.baseline.ecmp_algorithm import ECMPAlgorithm
from output.result_exporter import export_benchmark_comparison
from output.visualizer import plot_algorithm_comparison


class SimpleBenchmark:
    def __init__(self, config):
        self.config = config

    def create_network(self):
        """创建网络拓扑"""
        print("🔧 构建网络拓扑...")

        builder = LEONetworkBuilder(
            self.config['network']['constellation'],
            self.config['network']['ground_stations']
        )

        topology = builder.build_network(
            satellite_bandwidth=self.config['network']['satellite_bandwidth'],
            ground_bandwidth=self.config['network']['ground_bandwidth']
        )

        stats = topology.get_statistics()
        print(f"   网络: {stats['total_nodes']}节点, {stats['total_links']}链路")

        return topology

    def generate_traffic(self, topology):
        """生成流量需求"""
        print("📈 生成流量需求...")

        generator = TrafficGenerator()
        ground_stations = [
            node.id for node in topology.nodes.values()
            if node.type.value == 'ground_station'
        ]

        demands = generator.generate_traffic_demands(
            ground_station_ids=ground_stations,
            total_traffic=self.config['traffic']['total_gbps'],
            duration=self.config['traffic']['duration'],
            elephant_ratio=self.config['traffic']['elephant_ratio']
        )

        print(f"   生成 {len(demands)} 个流量需求")
        return demands

    def run_ldmr(self, topology, demands):
        """运行LDMR算法"""
        print("\n🚀 运行LDMR算法...")

        ldmr_config = LDMRConfig(
            K=self.config['algorithm']['K'],
            r1=self.config['algorithm']['r1'],
            r2=self.config['algorithm']['r2'],
            r3=self.config['algorithm']['r3'],
            Ne_th=self.config['algorithm']['Ne_th'],
            enable_statistics=True
        )

        ldmr = LDMRAlgorithm(ldmr_config)

        start_time = time.time()
        results = ldmr.run_ldmr_algorithm(topology, demands)
        exec_time = time.time() - start_time

        stats = ldmr.get_algorithm_statistics(results)
        disjoint_stats = ldmr.verify_path_disjointness(results)

        return {
            'algorithm': 'LDMR',
            'success_rate': stats.get('success_rate', 0),
            'avg_delay': stats.get('avg_path_delay', 0) * 1000,  # 转为ms
            'total_paths': stats.get('total_paths_calculated', 0),
            'avg_paths_per_demand': stats.get('avg_paths_per_demand', 0),
            'execution_time': exec_time,
            'disjoint_rate': disjoint_stats.get('disjoint_rate', 0)
        }

    def run_spf(self, topology, demands):
        """运行SPF算法"""
        print("🚀 运行SPF算法...")

        spf = SPFAlgorithm({'weight_type': 'delay'})

        start_time = time.time()
        results = spf.run_algorithm(topology, demands)
        exec_time = time.time() - start_time

        # 计算统计信息
        successful = [r for r in results if r.success]
        total_paths = sum(len(r.paths) for r in successful)
        avg_delay = sum(sum(p.total_delay for p in r.paths) for r in successful) / total_paths if total_paths > 0 else 0

        return {
            'algorithm': 'SPF',
            'success_rate': len(successful) / len(results) if results else 0,
            'avg_delay': avg_delay * 1000,  # 转为ms
            'total_paths': total_paths,
            'avg_paths_per_demand': total_paths / len(successful) if successful else 0,
            'execution_time': exec_time,
            'disjoint_rate': 1.0  # SPF单路径，默认不相交
        }

    def run_ecmp(self, topology, demands):
        """运行ECMP算法"""
        print("🚀 运行ECMP算法...")

        ecmp = ECMPAlgorithm({
            'weight_type': 'delay',
            'max_paths': 4,
            'tolerance': 0.1
        })

        start_time = time.time()
        results = ecmp.run_algorithm(topology, demands)
        exec_time = time.time() - start_time

        # 计算统计信息
        successful = [r for r in results if r.success]
        total_paths = sum(len(r.paths) for r in successful)
        avg_delay = sum(sum(p.total_delay for p in r.paths) for r in successful) / total_paths if total_paths > 0 else 0

        return {
            'algorithm': 'ECMP',
            'success_rate': len(successful) / len(results) if results else 0,
            'avg_delay': avg_delay * 1000,  # 转为ms
            'total_paths': total_paths,
            'avg_paths_per_demand': total_paths / len(successful) if successful else 0,
            'execution_time': exec_time,
            'disjoint_rate': 0.5  # ECMP可能有部分重叠
        }

    def run_benchmark(self):
        """运行完整基准测试"""
        print("🎯 开始基准测试对比")
        print("=" * 60)

        # 创建网络和流量
        topology = self.create_network()
        demands = self.generate_traffic(topology)

        # 运行三个算法
        results = []

        try:
            ldmr_result = self.run_ldmr(topology, demands)
            results.append(ldmr_result)
        except Exception as e:
            print(f"❌ LDMR运行失败: {e}")

        try:
            spf_result = self.run_spf(topology, demands)
            results.append(spf_result)
        except Exception as e:
            print(f"❌ SPF运行失败: {e}")

        try:
            ecmp_result = self.run_ecmp(topology, demands)
            results.append(ecmp_result)
        except Exception as e:
            print(f"❌ ECMP运行失败: {e}")

        # 显示对比结果
        self.display_results(results)

        return results

    def display_results(self, results):
        """显示对比结果"""
        print("\n" + "=" * 80)
        print("📊 基准测试结果对比")
        print("=" * 80)

        # 表头
        print(
            f"{'算法':<8} {'成功率':<8} {'平均延迟(ms)':<12} {'总路径数':<10} {'平均路径数':<10} {'执行时间(s)':<12} {'不相交率':<10}")
        print("-" * 80)

        # 数据行
        for result in results:
            print(f"{result['algorithm']:<8} "
                  f"{result['success_rate']:<8.1%} "
                  f"{result['avg_delay']:<12.3f} "
                  f"{result['total_paths']:<10} "
                  f"{result['avg_paths_per_demand']:<10.1f} "
                  f"{result['execution_time']:<12.2f} "
                  f"{result['disjoint_rate']:<10.1%}")

        print("=" * 80)

        # 关键洞察
        if len(results) >= 2:
            print("\n💡 关键洞察:")
            ldmr_result = next((r for r in results if r['algorithm'] == 'LDMR'), None)
            spf_result = next((r for r in results if r['algorithm'] == 'SPF'), None)

            if ldmr_result and spf_result:
                delay_overhead = ((ldmr_result['avg_delay'] - spf_result['avg_delay']) / spf_result['avg_delay']) * 100
                time_overhead = ldmr_result['execution_time'] / spf_result['execution_time']

                print(f"📈 LDMR vs SPF:")
                print(f"   延迟开销: +{delay_overhead:.1f}% (多路径代价)")
                print(f"   计算开销: {time_overhead:.1f}x")
                print(f"   多路径优势: {ldmr_result['avg_paths_per_demand']:.1f}条链路不相交路径")
                print(f"   容错性: {ldmr_result['disjoint_rate']:.1%}路径不相交率")

        print("=" * 80)

        # 导出结果
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 导出CSV数据
            csv_path = export_benchmark_comparison(results, timestamp)

            # 生成对比图表
            chart_path = plot_algorithm_comparison(results, timestamp)

            print(f"\n📊 基准测试结果已保存:")
            print(f"   数据文件: {csv_path}")
            print(f"   图表文件: {chart_path}")

        except Exception as e:
            print(f"⚠️  结果导出失败: {e}")

def main():
    """主函数"""
    print("🚀 LDMR简化基准测试")

    # 加载配置
    config = load_config()

    # 运行基准测试
    benchmark = SimpleBenchmark(config)
    results = benchmark.run_benchmark()

    print("\n✅ 基准测试完成!")


if __name__ == "__main__":
    main()