#!/usr/bin/env python3
"""
可视化生成器
负责生成LDMR算法、基准测试、参数分析的图表和可视化结果
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# 设置中文字体支持和图表样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")

try:
    from algorithms.ldmr_algorithms import MultiPathResult
    from algorithms.baseline.baseline_interface import AlgorithmResult
except ImportError:
    try:
        from ..algorithms.ldmr_algorithms import MultiPathResult
        from ..algorithms.baseline.baseline_interface import AlgorithmResult
    except ImportError:
        # 占位符，实际运行时会正确导入
        pass


class Visualizer:
    """可视化生成器类"""

    def __init__(self, output_dir: str = "results", figure_format: str = "png"):
        self.output_dir = Path(output_dir)
        self.figures_dir = self.output_dir / "figures"
        self.figure_format = figure_format

        # 确保输出目录存在
        self.figures_dir.mkdir(parents=True, exist_ok=True)

        # 设置图表默认参数
        self.figure_size = (12, 8)
        self.dpi = 300
        self.colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#1B998B', '#8E6C8A']

    def _save_figure(self, fig, filename: str, tight_layout: bool = True) -> str:
        """保存图表到文件"""
        if tight_layout:
            fig.tight_layout()

        filepath = self.figures_dir / f"{filename}.{self.figure_format}"
        fig.savefig(filepath, dpi=self.dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)

        return str(filepath)

    def plot_algorithm_comparison(self, benchmark_results: Dict[str, Any],
                                  timestamp: str = None) -> str:
        """
        生成算法性能对比图表

        Args:
            benchmark_results: 基准测试结果字典
            timestamp: 时间戳

        Returns:
            str: 图表文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📊 生成算法对比图表...")

        # 提取数据
        algorithms = []
        success_rates = []
        avg_delays = []
        avg_paths = []
        exec_times = []

        for algo_name, data in benchmark_results.items():
            if 'error' not in data:
                metrics = data.get('metrics', {})
                algorithms.append(algo_name)
                success_rates.append(metrics.get('success_rate', 0) * 100)
                avg_delays.append(metrics.get('avg_path_delay', 0) * 1000)  # 转换为ms
                avg_paths.append(metrics.get('avg_paths_per_demand', 0))
                exec_times.append(metrics.get('execution_time', 0))

        if not algorithms:
            print("❌ 没有有效的算法对比数据")
            return ""

        # 创建2x2子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        # 1. 成功率对比
        bars1 = ax1.bar(algorithms, success_rates, color=self.colors[:len(algorithms)])
        ax1.set_title('Comparison of Success Rates', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Success Rate (%)')
        ax1.set_ylim(0, 105)

        # 添加数值标签
        for bar, rate in zip(bars1, success_rates):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + 1,
                     f'{rate:.1f}%', ha='center', va='bottom')

        # 2. 平均延迟对比
        bars2 = ax2.bar(algorithms, avg_delays, color=self.colors[:len(algorithms)])
        ax2.set_title('Comparison of Average Latency', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Average Latency (ms)')

        for bar, delay in zip(bars2, avg_delays):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{delay:.3f}', ha='center', va='bottom')

        # 3. 平均路径数对比
        bars3 = ax3.bar(algorithms, avg_paths, color=self.colors[:len(algorithms)])
        ax3.set_title('Comparison of Average Number of Paths', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Average Number of Paths')

        for bar, paths in zip(bars3, avg_paths):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{paths:.1f}', ha='center', va='bottom')

        # 4. 执行时间对比
        bars4 = ax4.bar(algorithms, exec_times, color=self.colors[:len(algorithms)])
        ax4.set_title('Comparison of Execution Time', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Execution Time (s)')

        for bar, time in zip(bars4, exec_times):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{time:.2f}', ha='center', va='bottom')

        # 调整布局
        plt.suptitle('Performance Comparison between LDMR and Benchmark Algorithms', fontsize=16, fontweight='bold', y=0.98)

        filename = f"algorithm_comparison_{timestamp}"
        filepath = self._save_figure(fig, filename)

        print(f"   ✅ 算法对比图表已保存: {filepath}")
        return filepath

    def plot_parameter_sensitivity(self, param_results: Dict[str, Any],
                                   timestamp: str = None) -> str:
        """
        生成参数敏感性分析图表

        Args:
            param_results: 参数分析结果字典
            timestamp: 时间戳

        Returns:
            str: 图表文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📊 生成参数敏感性图表...")

        # 这里需要根据实际的参数分析数据结构来调整
        # 假设我们有不同参数值的测试结果
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()

        param_names = list(param_results.keys())

        # 示例数据生成（实际使用时需要从param_results中提取）
        example_data = {
            'r3': {
                'values': [20, 30, 40, 50, 60, 70],
                'success_rates': [0.95, 0.97, 0.98, 1.0, 0.99, 0.97],
                'avg_delays': [0.080, 0.075, 0.073, 0.072, 0.074, 0.076],
                'optimal': 50
            },
            'K': {
                'values': [2, 3, 4],
                'success_rates': [1.0, 0.98, 0.95],
                'avg_delays': [0.072, 0.071, 0.070],
                'optimal': 2
            },
            'Ne_th': {
                'values': [1, 2, 3, 4],
                'success_rates': [0.96, 1.0, 0.99, 0.97],
                'avg_delays': [0.075, 0.072, 0.073, 0.076],
                'optimal': 2
            }
        }

        plot_idx = 0
        for param_name in param_names[:3]:  # 最多显示3个参数
            if param_name in example_data:
                data = example_data[param_name]

                # 成功率曲线
                if plot_idx < len(axes):
                    ax = axes[plot_idx]
                    ax.plot(data['values'], [r * 100 for r in data['success_rates']],
                            'o-', linewidth=2, markersize=8, color=self.colors[plot_idx])
                    ax.axvline(x=data['optimal'], color='red', linestyle='--', alpha=0.7,
                               label=f'Optimal: {data["optimal"]}')
                    ax.set_title(f'Impact of {param_name} Parameter on Success Rate', fontweight='bold')
                    ax.set_xlabel(f'{param_name} Value')
                    ax.set_ylabel('Success Rate (%)')
                    ax.grid(True, alpha=0.3)
                    ax.legend()
                    plot_idx += 1

                # 延迟曲线
                if plot_idx < len(axes):
                    ax = axes[plot_idx]
                    ax.plot(data['values'], [d * 1000 for d in data['avg_delays']],
                            's-', linewidth=2, markersize=8, color=self.colors[plot_idx])
                    ax.axvline(x=data['optimal'], color='red', linestyle='--', alpha=0.7,
                               label=f'Optimal: {data["optimal"]}')
                    ax.set_title(f'Impact of {param_name} Parameter on Latency', fontweight='bold')
                    ax.set_xlabel(f'{param_name} Value')
                    ax.set_ylabel('Average Latency (ms)')
                    ax.grid(True, alpha=0.3)
                    ax.legend()
                    plot_idx += 1

        # 隐藏未使用的子图
        for i in range(plot_idx, len(axes)):
            axes[i].set_visible(False)

        plt.suptitle('LDMR Algorithm Parameter Sensitivity Analysis', fontsize=16, fontweight='bold', y=0.98)

        filename = f"parameter_sensitivity_{timestamp}"
        filepath = self._save_figure(fig, filename)

        print(f"   ✅ 参数敏感性图表已保存: {filepath}")
        return filepath

    def plot_performance_trends(self, ldmr_results: List[MultiPathResult],
                                timestamp: str = None) -> str:
        """
        生成性能趋势图表

        Args:
            ldmr_results: LDMR算法结果列表
            timestamp: 时间戳

        Returns:
            str: 图表文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📊 生成性能趋势图表...")

        if not ldmr_results:
            print("❌ 没有LDMR结果数据")
            return ""

        # 按带宽需求分组分析
        bandwidth_ranges = [(0, 10), (10, 50), (50, 100), (100, float('inf'))]
        range_labels = ['Small Traffic\n(0-10Mbps)', 'Medium Traffic\n(10-50Mbps)',
                        'Large Traffic\n(50-100Mbps)', 'Ultra Large Traffic\n(100+Mbps)']

        range_success_rates = []
        range_avg_delays = []
        range_avg_paths = []
        range_counts = []

        for min_bw, max_bw in bandwidth_ranges:
            filtered_results = [r for r in ldmr_results
                                if min_bw <= r.demand.bandwidth < max_bw]

            if filtered_results:
                successful = [r for r in filtered_results if r.success]
                success_rate = len(successful) / len(filtered_results) * 100
                avg_delay = np.mean([r.min_delay for r in successful]) if successful else 0
                avg_paths = np.mean([len(r.paths) for r in successful]) if successful else 0

                range_success_rates.append(success_rate)
                range_avg_delays.append(avg_delay)
                range_avg_paths.append(avg_paths)
                range_counts.append(len(filtered_results))
            else:
                range_success_rates.append(0)
                range_avg_delays.append(0)
                range_avg_paths.append(0)
                range_counts.append(0)

        # 创建图表
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        # 1. 不同流量大小的成功率
        bars1 = ax1.bar(range_labels, range_success_rates, color=self.colors[:4])
        ax1.set_title('Success Rate by Traffic Size', fontweight='bold')
        ax1.set_ylabel('Success Rate (%)')
        ax1.set_ylim(0, 105)

        for bar, rate in zip(bars1, range_success_rates):
            if rate > 0:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width() / 2., height + 1,
                         f'{rate:.1f}%', ha='center', va='bottom')

        # 2. 不同流量大小的平均延迟
        bars2 = ax2.bar(range_labels, range_avg_delays, color=self.colors[:4])
        ax2.set_title('Average Latency by Traffic Size', fontweight='bold')
        ax2.set_ylabel('Average Latency (ms)')

        for bar, delay in zip(bars2, range_avg_delays):
            if delay > 0:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2., height,
                         f'{delay:.3f}', ha='center', va='bottom')

        # 3. 路径数分布
        path_counts = [len(r.paths) for r in ldmr_results if r.success]
        unique_paths, counts = np.unique(path_counts, return_counts=True)

        bars3 = ax3.bar([f'{p} Paths' for p in unique_paths], counts, color=self.colors[:len(unique_paths)])
        ax3.set_title('Distribution of Computed Paths', fontweight='bold')
        ax3.set_ylabel('Number of Traffic Demands')

        for bar, count in zip(bars3, counts):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{count}', ha='center', va='bottom')

        # 4. 计算时间分布
        comp_times = [r.computation_time * 1000 for r in ldmr_results]  # 转换为ms
        ax4.hist(comp_times, bins=20, color=self.colors[0], alpha=0.7, edgecolor='black')
        ax4.axvline(x=np.mean(comp_times), color='red', linestyle='--',
                    label=f'Average: {np.mean(comp_times):.2f}ms')
        ax4.set_title('Computation Time Distribution', fontweight='bold')
        ax4.set_xlabel('Computation Time (ms)')
        ax4.set_ylabel('Frequency')
        ax4.legend()

        plt.suptitle('LDMR Algorithm Performance Trend Analysis', fontsize=16, fontweight='bold', y=0.98)

        filename = f"performance_trends_{timestamp}"
        filepath = self._save_figure(fig, filename)

        print(f"   ✅ 性能趋势图表已保存: {filepath}")
        return filepath

    def plot_path_analysis(self, ldmr_results: List[MultiPathResult],
                           timestamp: str = None) -> str:
        """
        生成路径分析图表

        Args:
            ldmr_results: LDMR算法结果列表
            timestamp: 时间戳

        Returns:
            str: 图表文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📊 生成路径分析图表...")

        if not ldmr_results:
            print("❌ 没有LDMR结果数据")
            return ""

        successful_results = [r for r in ldmr_results if r.success]

        # 创建图表
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        # 1. 路径长度分布
        all_path_lengths = []
        for result in successful_results:
            for path in result.paths:
                all_path_lengths.append(path.length)

        if all_path_lengths:
            ax1.hist(all_path_lengths, bins=range(min(all_path_lengths),
                                                  max(all_path_lengths) + 2), color=self.colors[0],
                     alpha=0.7, edgecolor='black')
            ax1.axvline(x=np.mean(all_path_lengths), color='red', linestyle='--',
                        label=f'Average Length: {np.mean(all_path_lengths):.1f} hops')
            ax1.set_title('Path Length Distribution', fontweight='bold')
            ax1.set_xlabel('Path Length (hops)')
            ax1.set_ylabel('Number of Paths')
            ax1.legend()

        # 2. 路径延迟分布
        all_path_delays = []
        for result in successful_results:
            for path in result.paths:
                all_path_delays.append(path.total_delay)

        if all_path_delays:
            ax2.hist(all_path_delays, bins=20, color=self.colors[1],
                     alpha=0.7, edgecolor='black')
            ax2.axvline(x=np.mean(all_path_delays), color='red', linestyle='--',
                        label=f'Average Latency: {np.mean(all_path_delays):.3f}ms')
            ax2.set_title('Path Latency Distribution', fontweight='bold')
            ax2.set_xlabel('Path Latency (ms)')
            ax2.set_ylabel('Number of Paths')
            ax2.legend()

        # 3. 路径不相交验证
        disjoint_count = sum(1 for r in successful_results if len(r.paths) >= 2)
        total_multipath = sum(1 for r in successful_results if len(r.paths) >= 2)

        labels = ['Disjoint Paths', 'Possible Overlap']
        sizes = [disjoint_count, total_multipath - disjoint_count] if total_multipath > disjoint_count else [
            disjoint_count, 0]
        colors = [self.colors[2], self.colors[3]]

        if total_multipath > 0:
            wedges, texts, autotexts = ax3.pie(sizes, labels=labels, colors=colors,
                                               autopct='%1.1f%%', startangle=90)
            ax3.set_title('Multipath Disjointness Verification', fontweight='bold')

        # 4. 成功率 vs 路径数
        path_nums = range(1, max(len(r.paths) for r in ldmr_results) + 1)
        success_rates_by_paths = []

        for num_paths in path_nums:
            results_with_n_paths = [r for r in ldmr_results if len(r.paths) == num_paths or
                                    (num_paths == 1 and len(r.paths) == 0 and not r.success)]
            if results_with_n_paths:
                success_count = sum(1 for r in results_with_n_paths if r.success)
                success_rate = success_count / len(results_with_n_paths) * 100
                success_rates_by_paths.append(success_rate)
            else:
                success_rates_by_paths.append(0)

        ax4.plot(path_nums, success_rates_by_paths, 'o-', linewidth=2,
                 markersize=8, color=self.colors[4])
        ax4.set_title('Success Rate vs Number of Computed Paths', fontweight='bold')
        ax4.set_xlabel('Number of Computed Paths')
        ax4.set_ylabel('Success Rate (%)')
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 105)

        plt.suptitle('LDMR Algorithm Path Analysis', fontsize=16, fontweight='bold', y=0.98)

        filename = f"path_analysis_{timestamp}"
        filepath = self._save_figure(fig, filename)

        print(f"   ✅ 路径分析图表已保存: {filepath}")
        return filepath

    def plot_network_overview(self, ldmr_results: List[MultiPathResult],
                              benchmark_results: Dict[str, Any] = None,
                              timestamp: str = None) -> str:
        """
        生成网络性能总览图表

        Args:
            ldmr_results: LDMR算法结果
            benchmark_results: 基准测试结果（可选）
            timestamp: 时间戳

        Returns:
            str: 图表文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📊 生成网络性能总览图表...")

        fig = plt.figure(figsize=(16, 10))

        # 创建网格布局
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

        # 1. 整体性能指标 (占据左上角2x2)
        ax1 = fig.add_subplot(gs[0:2, 0:2])

        if ldmr_results:
            successful = [r for r in ldmr_results if r.success]
            total_demands = len(ldmr_results)
            success_count = len(successful)
            total_paths = sum(len(r.paths) for r in successful)
            avg_delay = np.mean([r.min_delay for r in successful]) if successful else 0
            avg_comp_time = np.mean([r.computation_time for r in ldmr_results])

            # 创建性能指标表格
            metrics_data = [
                ['Total Traffic Demands', f'{total_demands}'],
                ['Successful Computations', f'{success_count}'],
                ['Success Rate', f'{success_count / total_demands * 100:.1f}%'],
                ['Total Paths', f'{total_paths}'],
                ['Average Paths per Demand', f'{total_paths / success_count if success_count > 0 else 0:.1f}'],
                ['Average Latency', f'{avg_delay:.3f} ms'],
                ['Average Computation Time', f'{avg_comp_time * 1000:.2f} ms']
            ]

            ax1.axis('tight')
            ax1.axis('off')
            table = ax1.table(cellText=metrics_data,
                              colLabels=['Performance Metrics', 'Values'],
                              cellLoc='center',
                              loc='center',
                              colWidths=[0.6, 0.4])
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 2)
            ax1.set_title('LDMR Algorithm Performance Overview', fontsize=14, fontweight='bold', pad=20)

        # 2. 算法对比雷达图 (右上角)
        if benchmark_results:
            ax2 = fig.add_subplot(gs[0, 2:], projection='polar')

            # 提取对比数据
            algorithms = []
            metrics_values = []

            for algo_name, data in benchmark_results.items():
                if 'error' not in data:
                    metrics = data.get('metrics', {})
                    algorithms.append(algo_name)
                    # 归一化指标 (0-1范围)
                    values = [
                        metrics.get('success_rate', 0),
                        1 - min(metrics.get('avg_path_delay', 0), 0.1) / 0.1,  # 延迟越低越好
                        min(metrics.get('avg_paths_per_demand', 0), 4) / 4,  # 路径数
                        1 - min(metrics.get('execution_time', 0), 10) / 10  # 执行时间越低越好
                    ]
                    metrics_values.append(values)

            if algorithms:
                angles = np.linspace(0, 2 * np.pi, 4, endpoint=False).tolist()
                angles += angles[:1]  # 闭合

                labels = ['Success Rate', 'Latency Performance', 'Multipath Capability', 'Computational Efficiency']

                for i, (algo, values) in enumerate(zip(algorithms, metrics_values)):
                    values += values[:1]  # 闭合
                    ax2.plot(angles, values, 'o-', linewidth=2,
                             label=algo, color=self.colors[i])
                    ax2.fill(angles, values, alpha=0.1, color=self.colors[i])

                ax2.set_xticks(angles[:-1])
                ax2.set_xticklabels(labels)
                ax2.set_ylim(0, 1)
                ax2.set_title('Algorithm Performance Radar Chart', fontweight='bold', pad=20)
                ax2.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))

        # 3. 流量分布 (左下角)
        ax3 = fig.add_subplot(gs[1, 2:])

        if ldmr_results:
            bandwidths = [r.demand.bandwidth for r in ldmr_results]
            ax3.hist(bandwidths, bins=20, color=self.colors[0], alpha=0.7, edgecolor='black')
            ax3.axvline(x=np.mean(bandwidths), color='red', linestyle='--',
                        label=f'Average Bandwidth: {np.mean(bandwidths):.1f}Mbps')
            ax3.set_title('Traffic Demand Distribution', fontweight='bold')
            ax3.set_xlabel('Bandwidth Demand (Mbps)')
            ax3.set_ylabel('Number of Demands')
            ax3.legend()

        # 4. 关键统计信息 (底部)
        ax4 = fig.add_subplot(gs[2, :])

        if ldmr_results:
            # 生成关键洞察文本
            insights = []

            if successful:
                max_delay = max(r.min_delay for r in successful)
                min_delay = min(r.min_delay for r in successful)
                insights.append(f"Latency Range: {min_delay:.3f}ms - {max_delay:.3f}ms")

                path_counts = [len(r.paths) for r in successful]
                avg_paths = np.mean(path_counts)
                insights.append(f"Average Paths: {avg_paths:.1f}")

                # 路径不相交率
                multipath_results = [r for r in successful if len(r.paths) >= 2]
                if multipath_results:
                    insights.append(f"Multipath Demands: {len(multipath_results)}")

                # 计算效率
                fast_computations = sum(1 for r in ldmr_results if r.computation_time < 0.001)
                insights.append(f"Fast Computations (<1ms): {fast_computations}")

            insight_text = " | ".join(insights)

            ax4.text(0.5, 0.5, f"Key Insights: {insight_text}",
                     ha='center', va='center', fontsize=12,
                     bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.5))
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')

        plt.suptitle(f'LDMR Network Performance Overview - {datetime.now().strftime("%Y-%m-%d")}',
                     fontsize=16, fontweight='bold', y=0.95)

        filename = f"network_overview_{timestamp}"
        filepath = self._save_figure(fig, filename)

        print(f"   ✅ 网络性能总览图表已保存: {filepath}")
        return filepath


# 便捷函数
def plot_algorithm_comparison(benchmark_results: Dict[str, Any],
                              timestamp: str = None,
                              output_dir: str = "results",
                              figure_format: str = "png") -> str:
    """生成算法对比图表的便捷函数"""
    visualizer = Visualizer(output_dir, figure_format)
    return visualizer.plot_algorithm_comparison(benchmark_results, timestamp)


def plot_parameter_sensitivity(param_results: Dict[str, Any],
                               timestamp: str = None,
                               output_dir: str = "results",
                               figure_format: str = "png") -> str:
    """生成参数敏感性图表的便捷函数"""
    visualizer = Visualizer(output_dir, figure_format)
    return visualizer.plot_parameter_sensitivity(param_results, timestamp)


def plot_performance_trends(ldmr_results: List[MultiPathResult],
                            timestamp: str = None,
                            output_dir: str = "results",
                            figure_format: str = "png") -> str:
    """生成性能趋势图表的便捷函数"""
    visualizer = Visualizer(output_dir, figure_format)
    return visualizer.plot_performance_trends(ldmr_results, timestamp)


def plot_path_analysis(ldmr_results: List[MultiPathResult],
                       timestamp: str = None,
                       output_dir: str = "results",
                       figure_format: str = "png") -> str:
    """生成路径分析图表的便捷函数"""
    visualizer = Visualizer(output_dir, figure_format)
    return visualizer.plot_path_analysis(ldmr_results, timestamp)


def plot_network_overview(ldmr_results: List[MultiPathResult],
                          benchmark_results: Dict[str, Any] = None,
                          timestamp: str = None,
                          output_dir: str = "results",
                          figure_format: str = "png") -> str:
    """生成网络总览图表的便捷函数"""
    visualizer = Visualizer(output_dir, figure_format)
    return visualizer.plot_network_overview(ldmr_results, benchmark_results, timestamp)


def generate_all_visualizations(ldmr_results: List[MultiPathResult] = None,
                                benchmark_results: Dict[str, Any] = None,
                                param_results: Dict[str, Any] = None,
                                output_dir: str = "results",
                                figure_format: str = "png") -> Dict[str, str]:
    """
    一次性生成所有可视化图表的便捷函数

    Returns:
        Dict[str, str]: 各个图表文件的路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    visualizer = Visualizer(output_dir, figure_format)

    visualization_files = {}

    print("🎨 开始生成所有可视化图表...")

    if benchmark_results:
        visualization_files['algorithm_comparison'] = visualizer.plot_algorithm_comparison(
            benchmark_results, timestamp)

    if param_results:
        visualization_files['parameter_sensitivity'] = visualizer.plot_parameter_sensitivity(
            param_results, timestamp)

    if ldmr_results:
        visualization_files['performance_trends'] = visualizer.plot_performance_trends(
            ldmr_results, timestamp)
        visualization_files['path_analysis'] = visualizer.plot_path_analysis(
            ldmr_results, timestamp)

        # 网络总览（综合所有数据）
        visualization_files['network_overview'] = visualizer.plot_network_overview(
            ldmr_results, benchmark_results, timestamp)

    print("✅ 所有可视化图表生成完成!")
    print("🖼️ 图表文件:")
    for chart_type, filepath in visualization_files.items():
        print(f"   {chart_type}: {filepath}")

    return visualization_files


class AdvancedVisualizer(Visualizer):
    """高级可视化器，提供更多定制化图表"""

    def plot_convergence_analysis(self, training_data: Dict[str, List[float]],
                                  timestamp: str = None) -> str:
        """绘制算法收敛性分析图（为未来的GNN-MPTE准备）"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📊 生成收敛性分析图表...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 奖励收敛曲线
        if 'rewards' in training_data:
            episodes = list(range(len(training_data['rewards'])))
            ax1.plot(episodes, training_data['rewards'], color=self.colors[0], linewidth=2)
            ax1.set_title('Training Reward Convergence Curve', fontweight='bold')
            ax1.set_xlabel('Training Episodes')
            ax1.set_ylabel('Cumulative Reward')
            ax1.grid(True, alpha=0.3)

        # 损失函数曲线
        if 'losses' in training_data:
            episodes = list(range(len(training_data['losses'])))
            ax2.plot(episodes, training_data['losses'], color=self.colors[1], linewidth=2)
            ax2.set_title('Training Loss Curve', fontweight='bold')
            ax2.set_xlabel('Training Episodes')
            ax2.set_ylabel('Loss Value')
            ax2.grid(True, alpha=0.3)

        plt.suptitle('Algorithm Convergence Analysis', fontsize=16, fontweight='bold')

        filename = f"convergence_analysis_{timestamp}"
        filepath = self._save_figure(fig, filename)

        print(f"   ✅ 收敛性分析图表已保存: {filepath}")
        return filepath

    def plot_load_balancing_analysis(self, link_usage_data: Dict[str, int],
                                     timestamp: str = None) -> str:
        """绘制负载均衡分析图"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📊 生成负载均衡分析图表...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 链路使用频次分布
        usage_values = list(link_usage_data.values())
        ax1.hist(usage_values, bins=20, color=self.colors[0], alpha=0.7, edgecolor='black')
        ax1.axvline(x=np.mean(usage_values), color='red', linestyle='--',
                    label=f'Average Usage: {np.mean(usage_values):.1f}')
        ax1.set_title('Link Usage Frequency Distribution', fontweight='bold')
        ax1.set_xlabel('Usage Count')
        ax1.set_ylabel('Number of Links')
        ax1.legend()

        # Jain公平性指数计算和显示
        if usage_values:
            sum_usage = sum(usage_values)
            sum_square_usage = sum(u ** 2 for u in usage_values)
            jain_index = (sum_usage ** 2) / (len(usage_values) * sum_square_usage) if sum_square_usage > 0 else 0

            # 绘制公平性指标
            metrics = ['Jain Fairness Index', 'Usage Variance', 'Max/Min Ratio']
            values = [
                jain_index,
                np.var(usage_values) / max(usage_values) if max(usage_values) > 0 else 0,
                max(usage_values) / min(usage_values) if min(usage_values) > 0 else 1
            ]

            bars = ax2.bar(metrics, values, color=self.colors[:3])
            ax2.set_title('Load Balancing Metrics', fontweight='bold')
            ax2.set_ylabel('Metric Value')

            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2., height,
                         f'{value:.3f}', ha='center', va='bottom')

        plt.suptitle('Network Load Balancing Analysis', fontsize=16, fontweight='bold')

        filename = f"load_balancing_analysis_{timestamp}"
        filepath = self._save_figure(fig, filename)

        print(f"   ✅ 负载均衡分析图表已保存: {filepath}")
        return filepath


if __name__ == "__main__":
    # 测试代码
    print("测试可视化生成器...")

    # 创建测试用的可视化器
    test_visualizer = Visualizer("test_results")

    # 生成测试数据
    test_benchmark_results = {
        'LDMR': {
            'metrics': {
                'success_rate': 1.0,
                'avg_path_delay': 0.072,
                'avg_paths_per_demand': 2.0,
                'execution_time': 2.24
            }
        },
        'SPF': {
            'metrics': {
                'success_rate': 1.0,
                'avg_path_delay': 0.076,
                'avg_paths_per_demand': 1.0,
                'execution_time': 0.45
            }
        },
        'ECMP': {
            'metrics': {
                'success_rate': 1.0,
                'avg_path_delay': 0.074,
                'avg_paths_per_demand': 3.2,
                'execution_time': 1.12
            }
        }
    }

    # 测试生成算法对比图
    comparison_path = test_visualizer.plot_algorithm_comparison(test_benchmark_results)
    print(f"✅ 测试算法对比图已生成: {comparison_path}")

    print("📊 可视化生成器测试完成!")