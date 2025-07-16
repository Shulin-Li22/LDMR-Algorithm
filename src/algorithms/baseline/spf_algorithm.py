"""
SPF (Shortest Path First) 算法实现
传统的单路径最短路径算法
"""

import time
from typing import List, Dict

try:
    from topology.topology_base import NetworkTopology
    from traffic.traffic_model import TrafficDemand
    from algorithms.basic_algorithms import DijkstraPathFinder, PathInfo
except ImportError:
    try:
        from ..topology.topology_base import NetworkTopology
        from ..traffic.traffic_model import TrafficDemand
        from .basic_algorithms import DijkstraPathFinder, PathInfo
    except ImportError:
        from topology_base import NetworkTopology
        from traffic_model import TrafficDemand
        from basic_algorithms import DijkstraPathFinder, PathInfo

from .baseline_interface import BaselineAlgorithm, AlgorithmResult


class SPFAlgorithm(BaselineAlgorithm):
    """
    SPF (Shortest Path First) 算法
    
    特点：
    - 为每个流量需求计算单一最短路径
    - 基于链路延迟选择路径
    - 简单快速，但容易造成负载不均
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.name = "SPF"
        self.weight_type = config.get('weight_type', 'delay') if config else 'delay'
        
    def calculate_paths_for_demand(self, topology: NetworkTopology, 
                                  demand: TrafficDemand) -> AlgorithmResult:
        """为单个流量需求计算最短路径"""
        start_time = time.time()
        
        try:
            # 使用Dijkstra算法计算最短路径
            path_finder = DijkstraPathFinder(topology)
            path = path_finder.find_shortest_path(
                demand.source_id, 
                demand.destination_id, 
                weight_type=self.weight_type
            )
            
            computation_time = time.time() - start_time
            
            if path:
                return AlgorithmResult(
                    algorithm_name=self.name,
                    demand=demand,
                    paths=[path],
                    success=True,
                    computation_time=computation_time,
                    metadata={
                        'weight_type': self.weight_type,
                        'path_delay': path.total_delay,
                        'path_length': path.length
                    }
                )
            else:
                return AlgorithmResult(
                    algorithm_name=self.name,
                    demand=demand,
                    paths=[],
                    success=False,
                    computation_time=computation_time,
                    metadata={'weight_type': self.weight_type}
                )
                
        except Exception as e:
            computation_time = time.time() - start_time
            return AlgorithmResult(
                algorithm_name=self.name,
                demand=demand,
                paths=[],
                success=False,
                computation_time=computation_time,
                metadata={'error': str(e)}
            )
    
    def get_algorithm_info(self) -> Dict:
        """获取SPF算法信息"""
        info = super().get_algorithm_info()
        info.update({
            'description': 'Shortest Path First - 基于延迟的单路径路由算法',
            'characteristics': [
                '计算单一最短路径',
                '基于链路延迟选择',
                '计算复杂度低',
                '容易造成负载不均'
            ],
            'weight_type': self.weight_type
        })
        return info


class SPFVariant(SPFAlgorithm):
    """SPF算法变体，支持不同权重类型"""
    
    def __init__(self, weight_type: str = 'delay', config: Dict = None):
        """
        Args:
            weight_type: 权重类型 ('delay', 'weight', 'hops')
            config: 其他配置参数
        """
        config = config or {}
        config['weight_type'] = weight_type
        super().__init__(config)
        self.name = f"SPF-{weight_type.upper()}"
        
    def get_algorithm_info(self) -> Dict:
        """获取算法信息"""
        info = super().get_algorithm_info()
        info['name'] = self.name
        info['description'] = f'SPF算法-{self.weight_type}权重'
        return info


# 预定义的SPF变体
SPF_Delay = lambda: SPFVariant('delay')
SPF_Weight = lambda: SPFVariant('weight') 
SPF_Hops = lambda: SPFVariant('hops')
