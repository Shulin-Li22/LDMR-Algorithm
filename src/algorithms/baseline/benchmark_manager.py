"""
基准测试管理器
管理多算法对比测试
"""

import time
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
import sys

# 添加路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from topology.topology_base import NetworkTopology
from traffic.traffic_model import TrafficDemand
from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig
from algorithms.baseline.spf_algorithm import SPFAlgorithm
from algorithms.baseline.ecmp_algorithm import ECMPAlgorithm
from algorithms.baseline.baseline_interface import AlgorithmResult


class BenchmarkManager:
    """基准测试管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.algorithms = {}
        self.results = {}
        
        # 注册默认算法
        self._register_default_algorithms()
    
    def _register_default_algorithms(self):
        """注册默认算法"""
        # LDMR算法
        ldmr_config = LDMRConfig(
            K=2, r1=1, r2=10, r3=50, Ne_th=2, enable_statistics=True
        )
        self.algorithms['LDMR'] = LDMRAlgorithm(ldmr_config)
        
        # SPF算法
        self.algorithms['SPF'] = SPFAlgorithm({'weight_type': 'delay'})
        
        # ECMP算法
        self.algorithms['ECMP'] = ECMPAlgorithm({'max_paths': 4, 'tolerance': 0.1})
    
    def register_algorithm(self, name: str, algorithm):
        """注册算法"""
        self.algorithms[name] = algorithm
    
    def _convert_ldmr_to_baseline_results(self, ldmr_results: List, algorithm_name: str) -> List[AlgorithmResult]:
        """将LDMR结果转换为基准算法结果格式"""
        baseline_results = []
        
        for result in ldmr_results:
            # 创建AlgorithmResult
            algo_result = AlgorithmResult(
                algorithm_name=algorithm_name,
                demand=result.demand,
                paths=result.paths,
                success=result.success,
                computation_time=result.computation_time,
                metadata={
                    'total_delay': result.total_delay,
                    'min_delay': result.min_delay,
                    'total_hops': result.total_hops
                }
            )
            baseline_results.append(algo_result)
        
        return baseline_results
    
    def run_single_algorithm(self, algorithm_name: str, topology: NetworkTopology, 
                           traffic_demands: List[TrafficDemand]) -> List[AlgorithmResult]:
        """运行单个算法"""
        if algorithm_name not in self.algorithms:
            raise ValueError(f"算法 {algorithm_name} 未注册")
        
        algorithm = self.algorithms[algorithm_name]
        
        print(f"🔄 运行 {algorithm_name} 算法...")
        start_time = time.time()
        
        if algorithm_name == 'LDMR':
            # LDMR算法特殊处理
            ldmr_results = algorithm.run_ldmr_algorithm(topology, traffic_demands)
            results = self._convert_ldmr_to_baseline_results(ldmr_results, algorithm_name)
        else:
            # 基准算法
            results = algorithm.run_algorithm(topology, traffic_demands)
        
        execution_time = time.time() - start_time
        
        # 计算性能指标
        metrics = self._calculate_metrics(results, algorithm_name, execution_time)
        
        print(f"✅ {algorithm_name} 完成: 成功率={metrics['success_rate']:.2%}, "
              f"延迟={metrics.get('avg_path_delay', 0):.3f}ms")
        
        return results, metrics
    
    def run_benchmark(self, topology: NetworkTopology, 
                     traffic_demands: List[TrafficDemand],
                     algorithms: List[str] = None) -> Dict[str, Any]:
        """运行基准测试"""
        if algorithms is None:
            algorithms = list(self.algorithms.keys())
        
        print(f"🚀 开始基准测试")
        print(f"   算法: {', '.join(algorithms)}")
        print(f"   流量需求: {len(traffic_demands)} 个")
        
        benchmark_results = {}
        
        for algorithm_name in algorithms:
            try:
                results, metrics = self.run_single_algorithm(
                    algorithm_name, topology, traffic_demands)
                
                benchmark_results[algorithm_name] = {
                    'results': results,
                    'metrics': metrics
                }
                
            except Exception as e:
                print(f"❌ {algorithm_name} 执行失败: {e}")
                benchmark_results[algorithm_name] = {
                    'results': [],
                    'metrics': {},
                    'error': str(e)
                }
        
        print(f"✅ 基准测试完成")
        return benchmark_results
    
    def _calculate_metrics(self, results: List[AlgorithmResult], 
                          algorithm_name: str, execution_time: float) -> Dict[str, Any]:
        """计算性能指标"""
        if not results:
            return {'algorithm_name': algorithm_name, 'execution_time': execution_time}
        
        successful_results = [r for r in results if r.success]
        
        metrics = {
            'algorithm_name': algorithm_name,
            'total_demands': len(results),
            'successful_demands': len(successful_results),
            'failed_demands': len(results) - len(successful_results),
            'success_rate': len(successful_results) / len(results),
            'execution_time': execution_time
        }
        
        if successful_results:
            # 路径统计
            all_paths = []
            for result in successful_results:
                all_paths.extend(result.paths)
            
            if all_paths:
                metrics.update({
                    'total_paths': len(all_paths),
                    'avg_paths_per_demand': len(all_paths) / len(successful_results),
                    'avg_path_length': np.mean([p.length for p in all_paths]),
                    'min_path_length': min(p.length for p in all_paths),
                    'max_path_length': max(p.length for p in all_paths),
                    'avg_path_delay': np.mean([p.total_delay for p in all_paths]),
                    'min_path_delay': min(p.total_delay for p in all_paths),
                    'max_path_delay': max(p.total_delay for p in all_paths),
                })
            
            # 计算时间统计
            computation_times = [r.computation_time for r in results if r.computation_time > 0]
            if computation_times:
                metrics.update({
                    'avg_computation_time': np.mean(computation_times),
                    'total_computation_time': sum(computation_times),
                    'max_computation_time': max(computation_times),
                })
        
        return metrics
    
    def generate_comparison_table(self, benchmark_results: Dict[str, Any]) -> str:
        """生成对比表格"""
        if not benchmark_results:
            return "没有基准测试结果"
        
        # 表头
        table = "算法性能对比表\n"
        table += "=" * 80 + "\n"
        table += f"{'算法':<10} {'成功率':<8} {'平均延迟(ms)':<12} {'平均路径数':<10} {'执行时间(s)':<12}\n"
        table += "-" * 80 + "\n"
        
        # 数据行
        for algorithm_name, data in benchmark_results.items():
            if 'error' in data:
                table += f"{algorithm_name:<10} {'ERROR':<8} {'N/A':<12} {'N/A':<10} {'N/A':<12}\n"
                continue
            
            metrics = data['metrics']
            success_rate = metrics.get('success_rate', 0)
            avg_delay = metrics.get('avg_path_delay', 0)
            avg_paths = metrics.get('avg_paths_per_demand', 0)
            exec_time = metrics.get('execution_time', 0)
            
            table += f"{algorithm_name:<10} {success_rate:<8.2%} {avg_delay:<12.3f} "
            table += f"{avg_paths:<10.1f} {exec_time:<12.2f}\n"
        
        table += "=" * 80
        return table
    
    def generate_detailed_report(self, benchmark_results: Dict[str, Any]) -> str:
        """生成详细报告"""
        report = "基准测试详细报告\n"
        report += "=" * 60 + "\n\n"
        
        for algorithm_name, data in benchmark_results.items():
            report += f"算法: {algorithm_name}\n"
            report += "-" * 30 + "\n"
            
            if 'error' in data:
                report += f"❌ 执行失败: {data['error']}\n\n"
                continue
            
            metrics = data['metrics']
            
            # 基础指标
            report += f"成功率: {metrics.get('success_rate', 0):.2%}\n"
            report += f"成功需求数: {metrics.get('successful_demands', 0)}\n"
            report += f"失败需求数: {metrics.get('failed_demands', 0)}\n"
            report += f"执行时间: {metrics.get('execution_time', 0):.2f}s\n"
            
            # 路径指标
            if metrics.get('total_paths', 0) > 0:
                report += f"总路径数: {metrics.get('total_paths', 0)}\n"
                report += f"平均路径数/需求: {metrics.get('avg_paths_per_demand', 0):.1f}\n"
                report += f"平均路径长度: {metrics.get('avg_path_length', 0):.1f} 跳\n"
                report += f"平均路径延迟: {metrics.get('avg_path_delay', 0):.3f}ms\n"
                report += f"最小路径延迟: {metrics.get('min_path_delay', 0):.3f}ms\n"
                report += f"最大路径延迟: {metrics.get('max_path_delay', 0):.3f}ms\n"
            
            # 计算时间指标
            if metrics.get('avg_computation_time'):
                report += f"平均计算时间: {metrics.get('avg_computation_time', 0):.4f}s\n"
                report += f"总计算时间: {metrics.get('total_computation_time', 0):.2f}s\n"
            
            report += "\n"
        
        return report
    
    def save_results(self, benchmark_results: Dict[str, Any], output_dir: str = "results"):
        """保存基准测试结果"""
        import json
        import os
        from datetime import datetime
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存详细结果
        results_file = os.path.join(output_dir, f"benchmark_results_{timestamp}.json")
        
        # 清理结果以便JSON序列化
        clean_results = {}
        for algo_name, data in benchmark_results.items():
            clean_results[algo_name] = {
                'metrics': data['metrics'],
                'error': data.get('error', None)
            }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, indent=2, ensure_ascii=False, default=str)
        
        # 保存对比表格
        table_file = os.path.join(output_dir, f"benchmark_table_{timestamp}.txt")
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_comparison_table(benchmark_results))
        
        # 保存详细报告
        report_file = os.path.join(output_dir, f"benchmark_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_detailed_report(benchmark_results))
        
        print(f"📊 基准测试结果已保存:")
        print(f"   详细结果: {results_file}")
        print(f"   对比表格: {table_file}")
        print(f"   详细报告: {report_file}")
        
        return results_file, table_file, report_file


def run_quick_benchmark(topology: NetworkTopology, traffic_demands: List[TrafficDemand],
                       algorithms: List[str] = None) -> Dict[str, Any]:
    """快速基准测试的便捷函数"""
    manager = BenchmarkManager()
    results = manager.run_benchmark(topology, traffic_demands, algorithms)
    
    # 显示对比表格
    print("\n" + manager.generate_comparison_table(results))
    
    return results
