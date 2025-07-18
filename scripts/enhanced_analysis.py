#!/usr/bin/env python3
"""
增强的基准测试结果分析工具
使用方法: python scripts/enhanced_analysis.py results/benchmark_results_XXXXXX.json
"""

import json
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_benchmark_results(filepath):
    """加载基准测试结果"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_jain_fairness_index(values):
    """计算Jain公平性指数"""
    if not values:
        return 0.0
    
    n = len(values)
    sum_x = sum(values)
    sum_x_squared = sum(x**2 for x in values)
    
    if sum_x_squared == 0:
        return 1.0
    
    return (sum_x ** 2) / (n * sum_x_squared)

def analyze_results_deeply(results):
    """深入分析基准测试结果"""
    
    print("🔍 深入分析基准测试结果")
    print("=" * 60)
    
    algorithms = list(results.keys())
    
    # 1. 基础指标对比
    print("\n📊 基础指标对比:")
    print(f"{'指标':<15} {'LDMR':<10} {'SPF':<10} {'ECMP':<10}")
    print("-" * 50)
    
    metrics = ['success_rate', 'avg_path_delay', 'avg_paths_per_demand', 'execution_time']
    metric_names = ['成功率', '平均延迟(ms)', '平均路径数', '执行时间(s)']
    
    for metric, name in zip(metrics, metric_names):
        values = []
        for algo in algorithms:
            if metric == 'success_rate':
                val = f"{results[algo]['metrics'][metric]:.1%}"
            elif metric == 'avg_path_delay':
                val = f"{results[algo]['metrics'][metric]*1000:.3f}"
            else:
                val = f"{results[algo]['metrics'][metric]:.2f}"
            values.append(val)
        
        print(f"{name:<15} {values[0]:<10} {values[1]:<10} {values[2]:<10}")
    
    # 2. 路径质量分析
    print("\n🛣️ 路径质量分析:")
    print(f"{'算法':<8} {'总路径':<8} {'平均长度':<10} {'最短路径':<10} {'最长路径':<10}")
    print("-" * 50)
    
    for algo in algorithms:
        metrics = results[algo]['metrics']
        total_paths = metrics.get('total_paths', 0)
        avg_length = metrics.get('avg_path_length', 0)
        min_length = metrics.get('min_path_length', 0)
        max_length = metrics.get('max_path_length', 0)
        
        print(f"{algo:<8} {total_paths:<8} {avg_length:<10.1f} {min_length:<10} {max_length:<10}")
    
    # 3. 延迟分布分析
    print("\n⏱️ 延迟分布分析:")
    print(f"{'算法':<8} {'最小延迟':<10} {'平均延迟':<10} {'最大延迟':<10} {'延迟范围':<10}")
    print("-" * 55)
    
    for algo in algorithms:
        metrics = results[algo]['metrics']
        min_delay = metrics.get('min_path_delay', 0) * 1000  # 转换为ms
        avg_delay = metrics.get('avg_path_delay', 0) * 1000
        max_delay = metrics.get('max_path_delay', 0) * 1000
        delay_range = max_delay - min_delay
        
        print(f"{algo:<8} {min_delay:<10.2f} {avg_delay:<10.2f} {max_delay:<10.2f} {delay_range:<10.2f}")
    
    # 4. 效率分析
    print("\n⚡ 效率分析:")
    print(f"{'算法':<8} {'每需求耗时(ms)':<15} {'每路径耗时(ms)':<15} {'相对效率':<10}")
    print("-" * 55)
    
    ldmr_time = results['LDMR']['metrics']['execution_time']
    
    for algo in algorithms:
        metrics = results[algo]['metrics']
        exec_time = metrics['execution_time']
        total_demands = metrics['total_demands']
        total_paths = metrics['total_paths']
        
        time_per_demand = (exec_time / total_demands) * 1000
        time_per_path = (exec_time / total_paths) * 1000
        relative_efficiency = ldmr_time / exec_time
        
        print(f"{algo:<8} {time_per_demand:<15.3f} {time_per_path:<15.3f} {relative_efficiency:<10.2f}")

def plot_comparison_charts(results, output_dir="results/figures"):
    """绘制对比图表"""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    algorithms = list(results.keys())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建子图
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('LDMR vs Baseline Algorithms Performance Comparison', fontsize=16, fontweight='bold')
    
    # 1. 延迟对比
    delays = [results[algo]['metrics']['avg_path_delay'] * 1000 for algo in algorithms]
    bars1 = ax1.bar(algorithms, delays, color=colors)
    ax1.set_title('Average Path Delay Comparison')
    ax1.set_ylabel('Delay (ms)')
    ax1.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar, delay in zip(bars1, delays):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{delay:.3f}', ha='center', va='bottom')
    
    # 2. 路径数量对比
    path_counts = [results[algo]['metrics']['avg_paths_per_demand'] for algo in algorithms]
    bars2 = ax2.bar(algorithms, path_counts, color=colors)
    ax2.set_title('Average Paths per Demand')
    ax2.set_ylabel('Paths per Demand')
    ax2.grid(True, alpha=0.3)
    
    for bar, count in zip(bars2, path_counts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{count:.1f}', ha='center', va='bottom')
    
    # 3. 执行时间对比
    exec_times = [results[algo]['metrics']['execution_time'] for algo in algorithms]
    bars3 = ax3.bar(algorithms, exec_times, color=colors)
    ax3.set_title('Execution Time Comparison')
    ax3.set_ylabel('Time (seconds)')
    ax3.grid(True, alpha=0.3)
    
    for bar, time in zip(bars3, exec_times):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{time:.2f}', ha='center', va='bottom')
    
    # 4. 路径长度分布对比
    path_lengths = [results[algo]['metrics']['avg_path_length'] for algo in algorithms]
    bars4 = ax4.bar(algorithms, path_lengths, color=colors)
    ax4.set_title('Average Path Length Comparison')
    ax4.set_ylabel('Hops')
    ax4.grid(True, alpha=0.3)
    
    for bar, length in zip(bars4, path_lengths):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{length:.1f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # 保存图表
    chart_file = f"{output_dir}/algorithm_comparison.png"
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"📊 对比图表已保存: {chart_file}")
    
    return chart_file

def generate_insights(results):
    """生成分析洞察"""
    
    print("\n💡 关键洞察:")
    print("=" * 40)
    
    ldmr_metrics = results['LDMR']['metrics']
    spf_metrics = results['SPF']['metrics']
    ecmp_metrics = results['ECMP']['metrics']
    
    # 1. 延迟分析
    ldmr_delay = ldmr_metrics['avg_path_delay'] * 1000
    spf_delay = spf_metrics['avg_path_delay'] * 1000
    ecmp_delay = ecmp_metrics['avg_path_delay'] * 1000
    
    delay_overhead = ((ldmr_delay - spf_delay) / spf_delay) * 100
    
    print(f"1. 📈 LDMR延迟比SPF高 {delay_overhead:.1f}%")
    print(f"   这是链路不相交约束的代价")
    
    # 2. 多路径优势
    ldmr_paths = ldmr_metrics['avg_paths_per_demand']
    spf_paths = spf_metrics['avg_paths_per_demand']
    
    print(f"\n2. 🛣️ LDMR提供 {ldmr_paths:.0f} 条链路不相交路径")
    print(f"   相比SPF的单路径，提供更好的容错性")
    
    # 3. 计算复杂度
    ldmr_time = ldmr_metrics['execution_time']
    spf_time = spf_metrics['execution_time']
    ecmp_time = ecmp_metrics['execution_time']
    
    print(f"\n3. ⚡ 计算复杂度:")
    print(f"   SPF: {spf_time:.2f}s (基准)")
    print(f"   LDMR: {ldmr_time:.2f}s ({ldmr_time/spf_time:.1f}x)")
    print(f"   ECMP: {ecmp_time:.2f}s ({ecmp_time/spf_time:.1f}x)")

def suggest_improvements():
    """建议改进方向"""
    
    print("\n🚀 改进建议:")
    print("=" * 40)
    
    print("1. 📊 增加压力测试:")
    print("   • 高流量负载测试 (15-25 Gbps)")
    print("   • 网络拥塞场景模拟")
    print("   • 瓶颈链路带宽限制")
    
    print("\n2. 🔧 增加故障测试:")
    print("   • 链路故障恢复测试")
    print("   • 节点故障容错测试")
    print("   • 动态拓扑变化测试")
    
    print("\n3. 📈 优化评估指标:")
    print("   • 负载均衡指数 (Jain's Fairness)")
    print("   • 网络利用率")
    print("   • 端到端吞吐量")

def main():
    """主函数"""
    
    if len(sys.argv) < 2:
        print("使用方法: python scripts/enhanced_analysis.py <results_file.json>")
        print("示例: python scripts/enhanced_analysis.py results/benchmark_results_20250717_233946.json")
        return
    
    results_file = sys.argv[1]
    
    try:
        # 加载结果
        print(f"📂 加载结果文件: {results_file}")
        results = load_benchmark_results(results_file)
        
        # 深入分析
        analyze_results_deeply(results)
        
        # 生成图表
        chart_file = plot_comparison_charts(results)
        
        # 生成洞察
        generate_insights(results)
        
        # 建议改进
        suggest_improvements()
        
        print(f"\n✅ 分析完成！图表已保存: {chart_file}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
