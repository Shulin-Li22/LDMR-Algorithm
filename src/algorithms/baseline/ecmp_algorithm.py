"""
ECMP (Equal Cost Multiple Path) 算法实现
等价多路径算法
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


class ECMPAlgorithm(BaselineAlgorithm):
    """
    ECMP (Equal Cost Multiple Path) 算法
    
    特点：
    - 找到多条等价（相同或相近代价）路径
    - 支持负载均衡
    - 比SPF更好的网络利用率
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.name = "ECMP"
        self.weight_type = config.get('weight_type', 'delay') if config else 'delay'
        self.max_paths = config.get('max_paths', 4) if config else 4
        self.tolerance = config.get('tolerance', 0.1) if config else 0.1  # 10%容差
        
    def calculate_paths_for_demand(self, topology: NetworkTopology, 
                                  demand: TrafficDemand) -> AlgorithmResult:
        """为单个流量需求计算等价多路径"""
        start_time = time.time()
        
        try:
            # 使用Dijkstra算法计算K条最短路径
            path_finder = DijkstraPathFinder(topology)
            k_paths = path_finder.find_k_shortest_paths(
                demand.source_id, 
                demand.destination_id, 
                k=self.max_paths,
                weight_type=self.weight_type
            )
            
            computation_time = time.time() - start_time
            
            if k_paths:
                # 筛选等价路径
                equal_cost_paths = self._filter_equal_cost_paths(k_paths)
                
                return AlgorithmResult(
                    algorithm_name=self.name,
                    demand=demand,
                    paths=equal_cost_paths,
                    success=True,
                    computation_time=computation_time,
                    metadata={
                        'weight_type': self.weight_type,
                        'max_paths': self.max_paths,
                        'tolerance': self.tolerance,
                        'total_k_paths': len(k_paths),
                        'equal_cost_paths': len(equal_cost_paths),
                        'min_cost': min(self._get_path_cost(p) for p in equal_cost_paths),
                        'max_cost': max(self._get_path_cost(p) for p in equal_cost_paths)
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
    
    def _get_path_cost(self, path: PathInfo) -> float:
        """获取路径代价"""
        if self.weight_type == 'delay':
            return path.total_delay
        elif self.weight_type == 'hops':
            return path.length
        else:
            # 对于weight类型，需要重新计算
            return path.total_delay  # 简化处理
    
    def _filter_equal_cost_paths(self, paths: List[PathInfo]) -> List[PathInfo]:
        """筛选等价路径"""
        if not paths:
            return []
        
        # 计算所有路径的代价
        path_costs = [(path, self._get_path_cost(path)) for path in paths]
        
        # 找到最小代价
        min_cost = min(cost for _, cost in path_costs)
        
        # 计算容差阈值
        threshold = min_cost * (1 + self.tolerance)
        
        # 筛选等价路径
        equal_cost_paths = [
            path for path, cost in path_costs 
            if cost <= threshold
        ]
        
        return equal_cost_paths
    
    def get_algorithm_info(self) -> Dict:
        """获取ECMP算法信息"""
        info = super().get_algorithm_info()
        info.update({
            'description': 'Equal Cost Multiple Path - 等价多路径负载均衡算法',
            'characteristics': [
                '计算多条等价路径',
                '支持负载均衡',
                '比SPF更好的网络利用率',
                '路径代价相近'
            ],
            'parameters': {
                'weight_type': self.weight_type,
                'max_paths': self.max_paths,
                'tolerance': self.tolerance
            }
        })
        return info


class ECMPVariant(ECMPAlgorithm):
    """ECMP算法变体，支持不同配置"""
    
    def __init__(self, weight_type: str = 'delay', max_paths: int = 4, 
                 tolerance: float = 0.1, config: Dict = None):
        """
        Args:
            weight_type: 权重类型 ('delay', 'weight', 'hops')
            max_paths: 最大路径数
            tolerance: 等价路径容差
            config: 其他配置参数
        """
        config = config or {}
        config.update({
            'weight_type': weight_type,
            'max_paths': max_paths,
            'tolerance': tolerance
        })
        super().__init__(config)
        self.name = f"ECMP-{weight_type.upper()}-{max_paths}P"
        
    def get_algorithm_info(self) -> Dict:
        """获取算法信息"""
        info = super().get_algorithm_info()
        info['name'] = self.name
        info['description'] = f'ECMP算法-{self.weight_type}权重-{self.max_paths}路径'
        return info


# 预定义的ECMP变体
ECMP_Delay_2P = lambda: ECMPVariant('delay', 2)
ECMP_Delay_4P = lambda: ECMPVariant('delay', 4)
ECMP_Hops_2P = lambda: ECMPVariant('hops', 2)
ECMP_Hops_4P = lambda: ECMPVariant('hops', 4)
