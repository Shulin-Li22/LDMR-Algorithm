"""
基准算法统一接口
定义所有基准算法的统一接口和数据结构
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import time

try:
    from topology.topology_base import NetworkTopology
    from traffic.traffic_model import TrafficDemand
    from algorithms.basic_algorithms import PathInfo
except ImportError:
    try:
        from ...topology.topology_base import NetworkTopology
        from ...traffic.traffic_model import TrafficDemand
        from ..basic_algorithms import PathInfo
    except ImportError:
        from topology_base import NetworkTopology
        from traffic_model import TrafficDemand
        from basic_algorithms import PathInfo


@dataclass
class AlgorithmResult:
    """算法结果统一数据结构"""
    algorithm_name: str
    demand: TrafficDemand
    paths: List[PathInfo]
    success: bool
    computation_time: float
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def total_delay(self) -> float:
        """所有路径总延迟"""
        return sum(path.total_delay for path in self.paths)
    
    @property
    def min_delay(self) -> float:
        """最短路径延迟"""
        return min(path.total_delay for path in self.paths) if self.paths else float('inf')
    
    @property
    def total_paths(self) -> int:
        """路径总数"""
        return len(self.paths)
    
    @property
    def avg_path_length(self) -> float:
        """平均路径长度"""
        return sum(path.length for path in self.paths) / len(self.paths) if self.paths else 0


class BaselineAlgorithm(ABC):
    """基准算法抽象基类"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        self.execution_stats = {
            'total_time': 0.0,
            'total_computations': 0,
            'successful_computations': 0,
            'failed_computations': 0
        }
    
    @abstractmethod
    def calculate_paths_for_demand(self, topology: NetworkTopology, 
                                  demand: TrafficDemand) -> AlgorithmResult:
        """
        为单个流量需求计算路径
        
        Args:
            topology: 网络拓扑
            demand: 流量需求
            
        Returns:
            AlgorithmResult: 算法结果
        """
        pass
    
    def run_algorithm(self, topology: NetworkTopology, 
                     traffic_demands: List[TrafficDemand]) -> List[AlgorithmResult]:
        """
        运行算法处理所有流量需求
        
        Args:
            topology: 网络拓扑
            traffic_demands: 流量需求列表
            
        Returns:
            List[AlgorithmResult]: 所有结果列表
        """
        print(f"🚀 开始运行 {self.name} 算法")
        print(f"   处理 {len(traffic_demands)} 个流量需求")
        
        start_time = time.time()
        results = []
        
        for i, demand in enumerate(traffic_demands):
            if (i + 1) % 1000 == 0:
                print(f"   进度: {i + 1}/{len(traffic_demands)}")
            
            result = self.calculate_paths_for_demand(topology, demand)
            results.append(result)
            
            # 更新统计
            self.execution_stats['total_computations'] += 1
            if result.success:
                self.execution_stats['successful_computations'] += 1
            else:
                self.execution_stats['failed_computations'] += 1
        
        total_time = time.time() - start_time
        self.execution_stats['total_time'] = total_time
        
        success_count = sum(1 for r in results if r.success)
        print(f"✅ {self.name} 算法完成 (耗时: {total_time:.2f}s)")
        print(f"   成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        return results
    
    def get_algorithm_info(self) -> Dict:
        """获取算法信息"""
        return {
            'name': self.name,
            'description': self.__doc__ or f"{self.name} 算法",
            'config': self.config,
            'execution_stats': self.execution_stats.copy()
        }
    
    def get_performance_metrics(self, results: List[AlgorithmResult]) -> Dict:
        """计算性能指标"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.success]
        
        # 基础统计
        metrics = {
            'algorithm_name': self.name,
            'total_demands': len(results),
            'successful_demands': len(successful_results),
            'failed_demands': len(results) - len(successful_results),
            'success_rate': len(successful_results) / len(results) if results else 0,
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
                    'avg_path_length': sum(p.length for p in all_paths) / len(all_paths),
                    'min_path_length': min(p.length for p in all_paths),
                    'max_path_length': max(p.length for p in all_paths),
                    'avg_path_delay': sum(p.total_delay for p in all_paths) / len(all_paths),
                    'min_path_delay': min(p.total_delay for p in all_paths),
                    'max_path_delay': max(p.total_delay for p in all_paths),
                })
            
            # 计算时间统计
            computation_times = [r.computation_time for r in results]
            metrics.update({
                'avg_computation_time': sum(computation_times) / len(computation_times),
                'total_computation_time': sum(computation_times),
                'max_computation_time': max(computation_times),
                'min_computation_time': min(computation_times),
            })
        
        return metrics
    
    def calculate_load_balancing(self, results: List[AlgorithmResult], 
                               topology: NetworkTopology) -> float:
        """计算负载均衡指数（Jain公平性指数）"""
        link_usage = {}
        
        for result in results:
            if result.success:
                for path in result.paths:
                    for link in path.links:
                        link_id = tuple(sorted(link))
                        link_usage[link_id] = link_usage.get(link_id, 0) + 1
        
        if not link_usage:
            return 0.0
        
        usage_values = list(link_usage.values())
        sum_usage = sum(usage_values)
        sum_square_usage = sum(u ** 2 for u in usage_values)
        
        if sum_square_usage == 0:
            return 0.0
        
        jain_index = (sum_usage ** 2) / (len(usage_values) * sum_square_usage)
        return jain_index
