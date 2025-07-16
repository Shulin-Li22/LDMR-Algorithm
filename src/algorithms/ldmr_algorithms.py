"""
LDMR (Link Disjoint Multipath Routing) 算法实现
基于论文 "A GNN-Enabled Multipath Routing Algorithm for Spatial-Temporal Varying LEO Satellite Networks"
Algorithm 1 的完整实现
"""

import random
import numpy as np
import time
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from topology.topology_base import NetworkTopology, Link
    from algorithms.basic_algorithms import DijkstraPathFinder, PathInfo
    from traffic.traffic_model import TrafficDemand
except ImportError:
    try:
        from ..topology.topology_base import NetworkTopology, Link
        from .basic_algorithms import DijkstraPathFinder, PathInfo
        from ..traffic.traffic_model import TrafficDemand
    except ImportError:
        from topology_base import NetworkTopology, Link
        from basic_algorithms import DijkstraPathFinder, PathInfo
        from traffic_model import TrafficDemand


@dataclass
class LDMRConfig:
    """LDMR算法配置参数"""
    K: int = 2  # 每个节点对的路径数量 (论文中K=2为最优)
    r1: int = 1  # 权重下界1
    r2: int = 10  # 权重下界2
    r3: int = 50  # 权重上界 (论文测试结果显示50为最优值)
    Ne_th: int = 2  # 链路利用频次阈值
    max_iterations: int = 10  # 最大迭代次数
    enable_statistics: bool = True  # 是否启用详细统计


@dataclass
class MultiPathResult:
    """多路径计算结果"""
    source_id: str
    destination_id: str
    paths: List[PathInfo]
    demand: TrafficDemand
    success: bool = True
    computation_time: float = 0.0  # 计算时间(秒)

    @property
    def total_delay(self) -> float:
        """所有路径的总延迟"""
        return sum(path.total_delay for path in self.paths)

    @property
    def min_delay(self) -> float:
        """最小路径延迟"""
        return min(path.total_delay for path in self.paths) if self.paths else float('inf')

    @property
    def total_hops(self) -> int:
        """所有路径的总跳数"""
        return sum(path.length for path in self.paths)

    def __str__(self):
        return f"MultiPath({self.source_id}->{self.destination_id}, {len(self.paths)} paths, {self.success})"


class LDMRAlgorithm:
    """LDMR算法主类 - 实现论文Algorithm 1"""

    def __init__(self, config: LDMRConfig = None):
        self.config = config or LDMRConfig()
        self.link_usage_count: Dict[Tuple[str, str], int] = {}
        self.calculated_paths: Dict[Tuple[str, str], List[PathInfo]] = {}
        self.execution_stats = {
            'total_time': 0.0,
            'path_calculations': 0,
            'weight_updates': 0,
            'link_removals': 0
        }

    def reset_algorithm_state(self):
        """重置算法状态 (Algorithm 1, Steps 1-5)"""
        self.link_usage_count.clear()
        self.calculated_paths.clear()
        if self.config.enable_statistics:
            self.execution_stats = {
                'total_time': 0.0,
                'path_calculations': 0,
                'weight_updates': 0,
                'link_removals': 0
            }

    def increment_link_usage(self, path: PathInfo):
        """增加路径上所有链路的使用计数 (Algorithm 1, Step 10)"""
        for link_tuple in path.links:
            link_id = tuple(sorted(link_tuple))
            self.link_usage_count[link_id] = self.link_usage_count.get(link_id, 0) + 1

            if self.config.enable_statistics:
                self.execution_stats['path_calculations'] += 1

    def get_link_usage_count(self, node1: str, node2: str) -> int:
        """获取链路的使用计数"""
        link_id = tuple(sorted([node1, node2]))
        return self.link_usage_count.get(link_id, 0)

    def update_weight_matrix(self, topology: NetworkTopology, excluded_links: Set[Tuple[str, str]] = None):
        """
        更新权重矩阵 (Algorithm 1, Steps 13-19)

        根据链路使用频次动态调整权重:
        - 使用频次 < Ne_th: 权重范围 [r1, r2] (较小权重，鼓励使用)
        - 使用频次 >= Ne_th: 权重范围 [r2, r3] (较大权重，避免过度使用)
        """
        excluded_links = excluded_links or set()
        weight_updates = {}

        for link_id, link in topology.links.items():
            # 跳过排除的链路
            if link_id in excluded_links:
                continue

            usage_count = self.get_link_usage_count(link.node1_id, link.node2_id)

            # Algorithm 1, Steps 14-18: 根据使用频次更新权重
            if usage_count < self.config.Ne_th:
                # 使用频次较低，分配较小权重 (r1, r2)
                new_weight = random.randint(self.config.r1, self.config.r2)
            else:
                # 使用频次较高，分配较大权重 (r2, r3)
                new_weight = random.randint(self.config.r2, self.config.r3)

            weight_updates[link_id] = new_weight

        # 批量更新权重
        topology.update_link_weights(weight_updates)

        if self.config.enable_statistics:
            self.execution_stats['weight_updates'] += len(weight_updates)

    def calculate_shortest_delay_paths(self, topology: NetworkTopology,
                                       traffic_demands: List[TrafficDemand]) -> Dict[Tuple[str, str], PathInfo]:
        """
        计算所有节点对的最短延迟路径 (Algorithm 1, Steps 6-10)

        使用Dijkstra算法基于链路延迟计算最短路径，为后续多路径计算提供第一条路径
        """
        shortest_paths = {}
        path_finder = DijkstraPathFinder(topology)

        # 提取所有唯一的源-目的节点对
        node_pairs = set((demand.source_id, demand.destination_id) for demand in traffic_demands)

        print(f"     计算 {len(node_pairs)} 个节点对的最短延迟路径...")

        for source, destination in node_pairs:
            path = path_finder.find_shortest_path(source, destination, weight_type='delay')
            if path:
                shortest_paths[(source, destination)] = path
                # 更新链路使用计数 (Algorithm 1, Step 10)
                self.increment_link_usage(path)

        return shortest_paths

    def find_backup_path_with_excluded_links(self, topology: NetworkTopology,
                                             source: str, destination: str,
                                             excluded_links: Set[Tuple[str, str]]) -> Optional[PathInfo]:
        """
        查找备用路径，排除指定链路 (Algorithm 1, Steps 23-28)

        创建临时拓扑移除已使用的链路，然后在更新权重后计算路径
        """
        # 创建拓扑副本
        temp_topology = topology.copy()

        # 移除排除的链路 (Algorithm 1, Step 24)
        for link_id in excluded_links:
            if len(link_id) == 2:
                temp_topology.remove_link(link_id[0], link_id[1])
                if self.config.enable_statistics:
                    self.execution_stats['link_removals'] += 1

        # 更新权重矩阵 (Algorithm 1, Steps 25-26)
        self.update_weight_matrix(temp_topology)

        # 在更新后的拓扑上查找路径 (Algorithm 1, Step 27)
        path_finder = DijkstraPathFinder(temp_topology)
        backup_path = path_finder.find_shortest_path(source, destination, weight_type='weight')

        return backup_path

    def calculate_multipath_for_single_demand(self, topology: NetworkTopology,
                                              demand: TrafficDemand,
                                              existing_shortest_paths: Dict[
                                                  Tuple[str, str], PathInfo]) -> MultiPathResult:
        """
        为单个流量需求计算多路径 (Algorithm 1, Steps 12-30 的核心逻辑)

        过程:
        1. 获取第一条路径(最短延迟路径)
        2. 迭代计算K-1条备用路径，每次排除之前路径使用的链路
        3. 确保所有路径都是链路不相交的
        """
        start_time = time.time()
        source, destination = demand.source_id, demand.destination_id
        paths = []

        # 第一条路径: 最短延迟路径 (Algorithm 1, Step 6-10的结果)
        node_pair = (source, destination)
        if node_pair in existing_shortest_paths:
            shortest_path = existing_shortest_paths[node_pair]
            paths.append(shortest_path)
        else:
            # 如果没有预计算的路径，现场计算
            path_finder = DijkstraPathFinder(topology)
            shortest_path = path_finder.find_shortest_path(source, destination, weight_type='delay')
            if shortest_path:
                paths.append(shortest_path)
                self.increment_link_usage(shortest_path)
            else:
                computation_time = time.time() - start_time
                return MultiPathResult(source, destination, [], demand, False, computation_time)

        # 计算备用路径 (K-1条) (Algorithm 1, Steps 23-30)
        for k in range(1, self.config.K):
            # 收集已使用的链路
            excluded_links = set()
            for path in paths:
                for link_tuple in path.links:
                    link_id = tuple(sorted(link_tuple))
                    excluded_links.add(link_id)

            # 查找备用路径
            backup_path = self.find_backup_path_with_excluded_links(
                topology, source, destination, excluded_links)

            if backup_path:
                paths.append(backup_path)
                # 更新链路使用计数
                self.increment_link_usage(backup_path)
            else:
                # 无法找到更多不相交路径，提前结束
                break

        computation_time = time.time() - start_time
        return MultiPathResult(source, destination, paths, demand, True, computation_time)

    def run_ldmr_algorithm(self, topology: NetworkTopology,
                           traffic_demands: List[TrafficDemand]) -> List[MultiPathResult]:
        """
        运行完整的LDMR算法 (Algorithm 1 完整实现)

        主要步骤:
        1. 初始化 (Steps 1-5)
        2. 计算所有节点对的最短延迟路径 (Steps 6-10)
        3. 按流量大小降序处理每个需求 (Steps 11-30)
        4. 为每个需求计算K条链路不相交路径
        """
        algorithm_start_time = time.time()

        print(f"🚀 开始运行LDMR算法 (Algorithm 1)")
        print(f"     配置参数: K={self.config.K}, Ne_th={self.config.Ne_th}, r3={self.config.r3}")
        print(f"     流量需求数量: {len(traffic_demands)}")

        # Steps 1-5: 初始化
        self.reset_algorithm_state()
        results = []

        # 初始化拓扑权重为链路延迟
        for link in topology.links.values():
            link.weight = link.delay

        # Steps 6-10: 计算所有节点对的最短延迟路径
        print(f"     Phase 1: 计算最短延迟路径...")
        shortest_paths = self.calculate_shortest_delay_paths(topology, traffic_demands)
        print(f"     找到 {len(shortest_paths)} 条最短延迟路径")

        # Steps 11-30: 按流量大小降序处理每个流量需求
        print(f"     Phase 2: 按带宽降序处理流量需求...")
        sorted_demands = sorted(traffic_demands, key=lambda x: x.bandwidth, reverse=True)

        if sorted_demands:
            print(
                f"     带宽范围: {sorted_demands[0].bandwidth:.1f}Mbps (最大) - {sorted_demands[-1].bandwidth:.1f}Mbps (最小)")

        for i, demand in enumerate(sorted_demands):
            print(f"     处理需求 {i + 1}/{len(sorted_demands)}: "
                  f"{demand.source_id}->{demand.destination_id} "
                  f"({demand.bandwidth:.1f}Mbps, 优先级{demand.priority})")

            # 为当前流量需求计算多路径 (Steps 12-30)
            result = self.calculate_multipath_for_single_demand(topology, demand, shortest_paths)
            results.append(result)

            if result.success:
                print(f"       ✅ 成功计算 {len(result.paths)} 条路径 "
                      f"(总延迟: {result.total_delay:.1f}ms, 总跳数: {result.total_hops})")
            else:
                print(f"       ❌ 路径计算失败")

        # 记录总执行时间
        total_time = time.time() - algorithm_start_time
        if self.config.enable_statistics:
            self.execution_stats['total_time'] = total_time

        print(f"✅ LDMR算法执行完成 (耗时: {total_time:.2f}秒)")
        return results

    def get_algorithm_statistics(self, results: List[MultiPathResult]) -> Dict:
        """获取算法执行的详细统计信息"""
        if not results:
            return {}

        total_demands = len(results)
        successful_results = [r for r in results if r.success]
        successful_demands = len(successful_results)

        # 路径统计
        all_paths = []
        for result in successful_results:
            all_paths.extend(result.paths)

        path_lengths = [p.length for p in all_paths]
        path_delays = [p.total_delay for p in all_paths]
        computation_times = [r.computation_time for r in results]

        # 基础统计
        stats = {
            'total_demands': total_demands,
            'successful_demands': successful_demands,
            'failed_demands': total_demands - successful_demands,
            'success_rate': successful_demands / total_demands if total_demands > 0 else 0,
            'total_paths_calculated': len(all_paths),
            'avg_paths_per_successful_demand': len(all_paths) / successful_demands if successful_demands > 0 else 0,
        }

        # 路径质量统计
        if path_lengths:
            stats.update({
                'avg_path_length': np.mean(path_lengths),
                'min_path_length': min(path_lengths),
                'max_path_length': max(path_lengths),
                'std_path_length': np.std(path_lengths),
            })

        if path_delays:
            stats.update({
                'avg_path_delay': np.mean(path_delays),
                'min_path_delay': min(path_delays),
                'max_path_delay': max(path_delays),
                'std_path_delay': np.std(path_delays),
            })

        # 性能统计
        if computation_times:
            stats.update({
                'avg_computation_time': np.mean(computation_times),
                'total_computation_time': sum(computation_times),
                'max_computation_time': max(computation_times),
            })

        # 链路使用统计
        if self.link_usage_count:
            usage_values = list(self.link_usage_count.values())
            stats.update({
                'total_links_used': len(self.link_usage_count),
                'max_link_usage': max(usage_values),
                'avg_link_usage': np.mean(usage_values),
                'link_usage_distribution': dict(self.link_usage_count),
            })

        # 算法执行统计
        if self.config.enable_statistics:
            stats.update({
                'algorithm_execution_stats': self.execution_stats.copy()
            })

        return stats

    def verify_path_disjointness(self, results: List[MultiPathResult]) -> Dict:
        """验证路径的链路不相交性"""
        verification_stats = {
            'total_results_checked': len(results),
            'disjoint_results': 0,
            'non_disjoint_results': 0,
            'disjoint_rate': 0.0,
            'conflicts': []
        }

        for result in results:
            if not result.success or len(result.paths) < 2:
                continue

            # 检查该结果中的路径是否链路不相交
            all_links = set()
            is_disjoint = True
            conflicts = []

            for i, path in enumerate(result.paths):
                for link_tuple in path.links:
                    link_id = tuple(sorted(link_tuple))
                    if link_id in all_links:
                        is_disjoint = False
                        conflicts.append(f"路径{i + 1}中的链路{link_id}与之前路径冲突")
                    all_links.add(link_id)

            if is_disjoint:
                verification_stats['disjoint_results'] += 1
            else:
                verification_stats['non_disjoint_results'] += 1
                verification_stats['conflicts'].extend(conflicts)

        total_checked = verification_stats['disjoint_results'] + verification_stats['non_disjoint_results']
        if total_checked > 0:
            verification_stats['disjoint_rate'] = verification_stats['disjoint_results'] / total_checked

        return verification_stats


def create_ldmr_config_for_scenario(scenario: str) -> LDMRConfig:
    """为不同场景创建LDMR配置"""
    configs = {
        'testing': LDMRConfig(K=2, r1=1, r2=5, r3=20, Ne_th=1),
        'light_load': LDMRConfig(K=2, r1=1, r2=10, r3=30, Ne_th=2),
        'heavy_load': LDMRConfig(K=2, r1=1, r2=10, r3=50, Ne_th=3),
        'high_reliability': LDMRConfig(K=3, r1=1, r2=15, r3=60, Ne_th=2),
        'performance': LDMRConfig(K=2, r1=1, r2=10, r3=50, Ne_th=2, enable_statistics=True)
    }

    return configs.get(scenario, LDMRConfig())


def run_ldmr_simulation(topology: NetworkTopology,
                        traffic_demands: List[TrafficDemand],
                        config: LDMRConfig = None,
                        scenario: str = 'performance') -> Tuple[List[MultiPathResult], Dict]:
    """
    运行LDMR仿真的便捷函数

    Args:
        topology: 网络拓扑
        traffic_demands: 流量需求列表
        config: LDMR配置 (可选)
        scenario: 预定义场景 (可选)

    Returns:
        Tuple[List[MultiPathResult], Dict]: (路径计算结果, 统计信息)
    """
    if config is None:
        config = create_ldmr_config_for_scenario(scenario)

    ldmr = LDMRAlgorithm(config)
    results = ldmr.run_ldmr_algorithm(topology, traffic_demands)
    statistics = ldmr.get_algorithm_statistics(results)

    return results, statistics