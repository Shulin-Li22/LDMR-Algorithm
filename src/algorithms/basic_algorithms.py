"""
基础路由算法实现
包括Dijkstra最短路径算法和图操作工具
"""

import heapq
import networkx as nx
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import numpy as np
import sys
import os

# 添加相对导入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from topology.topology_base import NetworkTopology, Node, Link
except ImportError:
    try:
        from .topology_base import NetworkTopology, Node, Link
    except ImportError:
        from topology_base import NetworkTopology, Node, Link


@dataclass
class PathInfo:
    """路径信息"""
    nodes: List[str]  # 节点序列
    links: List[Tuple[str, str]]  # 链路序列
    total_delay: float  # 总延迟
    total_distance: float  # 总跳数
    bandwidth: float  # 路径带宽（瓶颈带宽）

    @property
    def length(self) -> int:
        """路径长度（跳数）"""
        return len(self.links)

    def __str__(self):
        path_str = " -> ".join(self.nodes)
        return f"Path({path_str}, delay={self.total_delay:.2f}ms, hops={self.length})"

    def __repr__(self):
        return self.__str__()


class DijkstraPathFinder:
    """Dijkstra最短路径查找器"""

    def __init__(self, topology: NetworkTopology):
        self.topology = topology

    def find_shortest_path(self, source: str, destination: str,
                           weight_type: str = 'delay',
                           excluded_links: Set[Tuple[str, str]] = None) -> Optional[PathInfo]:
        """
        使用Dijkstra算法查找最短路径

        Args:
            source: 源节点ID
            destination: 目标节点ID
            weight_type: 权重类型 ('delay', 'weight', 'hops')
            excluded_links: 排除的链路集合

        Returns:
            PathInfo: 路径信息，如果不存在路径则返回None
        """
        if source not in self.topology.nodes or destination not in self.topology.nodes:
            return None

        if source == destination:
            return PathInfo([source], [], 0.0, 0.0, float('inf'))

        excluded_links = excluded_links or set()

        # 初始化距离和前驱
        distances = {node_id: float('inf') for node_id in self.topology.nodes}
        predecessors = {node_id: None for node_id in self.topology.nodes}
        distances[source] = 0.0

        # 优先队列：(距离, 节点ID)
        pq = [(0.0, source)]
        visited = set()

        while pq:
            current_dist, current_node = heapq.heappop(pq)

            if current_node in visited:
                continue

            visited.add(current_node)

            if current_node == destination:
                break

            # 检查所有邻居
            for neighbor_id in self.topology.get_neighbors(current_node):
                if neighbor_id in visited:
                    continue

                # 检查链路是否被排除
                link_id = tuple(sorted([current_node, neighbor_id]))
                if link_id in excluded_links:
                    continue

                link = self.topology.get_link(current_node, neighbor_id)
                if not link or not link.is_active:
                    continue

                # 计算权重
                if weight_type == 'delay':
                    edge_weight = link.delay
                elif weight_type == 'weight':
                    edge_weight = link.weight
                elif weight_type == 'hops':
                    edge_weight = 1.0
                else:
                    edge_weight = link.delay

                new_distance = current_dist + edge_weight

                if new_distance < distances[neighbor_id]:
                    distances[neighbor_id] = new_distance
                    predecessors[neighbor_id] = current_node
                    heapq.heappush(pq, (new_distance, neighbor_id))

        # 重构路径
        if distances[destination] == float('inf'):
            return None

        path = self._reconstruct_path(predecessors, source, destination)
        if not path:
            return None

        return self._create_path_info(path)

    def _reconstruct_path(self, predecessors: Dict[str, str],
                          source: str, destination: str) -> Optional[List[str]]:
        """重构路径"""
        path = []
        current = destination

        while current is not None:
            path.append(current)
            current = predecessors[current]

        if path[-1] != source:
            return None

        return list(reversed(path))

    def _create_path_info(self, node_path: List[str]) -> PathInfo:
        """创建路径信息对象"""
        if len(node_path) < 2:
            return PathInfo(node_path, [], 0.0, 0.0, float('inf'))

        links = []
        total_delay = 0.0
        min_bandwidth = float('inf')

        for i in range(len(node_path) - 1):
            node1, node2 = node_path[i], node_path[i + 1]
            link = self.topology.get_link(node1, node2)

            if link:
                links.append((node1, node2))
                total_delay += link.delay
                min_bandwidth = min(min_bandwidth, link.available_bandwidth)
            else:
                # 不应该发生，但为了安全起见
                min_bandwidth = 0.0

        return PathInfo(
            nodes=node_path,
            links=links,
            total_delay=total_delay,
            total_distance=len(links),
            bandwidth=min_bandwidth if min_bandwidth != float('inf') else 0.0
        )

    def find_k_shortest_paths(self, source: str, destination: str, k: int = 2,
                              weight_type: str = 'delay') -> List[PathInfo]:
        """
        查找K条最短路径（使用Yen算法的简化版本）

        Args:
            source: 源节点ID
            destination: 目标节点ID
            k: 路径数量
            weight_type: 权重类型

        Returns:
            List[PathInfo]: K条路径的列表
        """
        if k <= 0:
            return []

        paths = []

        # 第一条路径：标准最短路径
        first_path = self.find_shortest_path(source, destination, weight_type)
        if first_path:
            paths.append(first_path)
        else:
            return []

        # 候选路径集合
        candidates = []

        for path_idx in range(1, k):
            if not paths:
                break

            previous_path = paths[-1]

            # 尝试从前一条路径的每个节点开始寻找替代路径
            for i in range(len(previous_path.nodes) - 1):
                spur_node = previous_path.nodes[i]
                root_path = previous_path.nodes[:i + 1]

                # 收集需要排除的链路
                excluded_links = set()

                # 排除与之前路径共享根路径的路径的下一条边
                for existing_path in paths:
                    if (len(existing_path.nodes) > i and
                            existing_path.nodes[:i + 1] == root_path):
                        if i + 1 < len(existing_path.nodes):
                            next_node = existing_path.nodes[i + 1]
                            link_id = tuple(sorted([spur_node, next_node]))
                            excluded_links.add(link_id)

                # 查找从spur_node到目标的路径
                spur_path = self.find_shortest_path(
                    spur_node, destination, weight_type, excluded_links)

                if spur_path and len(spur_path.nodes) > 1:
                    # 合并根路径和支路径
                    total_nodes = root_path[:-1] + spur_path.nodes
                    total_links = []
                    total_delay = 0.0
                    min_bandwidth = float('inf')

                    # 重新计算完整路径的指标
                    for j in range(len(total_nodes) - 1):
                        node1, node2 = total_nodes[j], total_nodes[j + 1]
                        link = self.topology.get_link(node1, node2)
                        if link:
                            total_links.append((node1, node2))
                            total_delay += link.delay
                            min_bandwidth = min(min_bandwidth, link.available_bandwidth)

                    candidate_path = PathInfo(
                        nodes=total_nodes,
                        links=total_links,
                        total_delay=total_delay,
                        total_distance=len(total_links),
                        bandwidth=min_bandwidth if min_bandwidth != float('inf') else 0.0
                    )

                    # 检查是否已存在相同路径
                    is_duplicate = False
                    for existing_path in paths + [c for c, _ in candidates]:
                        if existing_path.nodes == candidate_path.nodes:
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        candidates.append((candidate_path, candidate_path.total_delay))

            # 选择延迟最小的候选路径
            if candidates:
                candidates.sort(key=lambda x: x[1])
                next_path, _ = candidates.pop(0)
                paths.append(next_path)
            else:
                break

        return paths


class LinkDisjointPathFinder:
    """链路不相交路径查找器"""

    def __init__(self, topology: NetworkTopology):
        self.topology = topology
        self.dijkstra = DijkstraPathFinder(topology)

    def find_link_disjoint_paths(self, source: str, destination: str,
                                 k: int = 2, weight_type: str = 'delay') -> List[PathInfo]:
        """
        查找K条链路不相交的路径

        Args:
            source: 源节点ID
            destination: 目标节点ID
            k: 路径数量
            weight_type: 权重类型

        Returns:
            List[PathInfo]: 链路不相交的路径列表
        """
        paths = []
        excluded_links = set()

        for i in range(k):
            # 查找避开已使用链路的路径
            path = self.dijkstra.find_shortest_path(
                source, destination, weight_type, excluded_links)

            if path:
                paths.append(path)
                # 将该路径的所有链路加入排除集合
                for link in path.links:
                    link_id = tuple(sorted(link))
                    excluded_links.add(link_id)
            else:
                break

        return paths

    def verify_link_disjoint(self, paths: List[PathInfo]) -> bool:
        """验证路径是否链路不相交"""
        all_links = set()

        for path in paths:
            for link in path.links:
                link_id = tuple(sorted(link))
                if link_id in all_links:
                    return False
                all_links.add(link_id)

        return True


class GraphOperations:
    """图操作工具类"""

    @staticmethod
    def create_subgraph(topology: NetworkTopology,
                        excluded_links: Set[Tuple[str, str]] = None,
                        excluded_nodes: Set[str] = None) -> NetworkTopology:
        """
        创建子图，排除指定的链路和节点

        Args:
            topology: 原始拓扑
            excluded_links: 排除的链路集合
            excluded_nodes: 排除的节点集合

        Returns:
            NetworkTopology: 子图拓扑
        """
        excluded_links = excluded_links or set()
        excluded_nodes = excluded_nodes or set()

        # 创建新的拓扑
        sub_topology = NetworkTopology()

        # 添加未排除的节点
        for node_id, node in topology.nodes.items():
            if node_id not in excluded_nodes:
                sub_topology.add_node(node)

        # 添加未排除的链路
        for link_id, link in topology.links.items():
            if (link_id not in excluded_links and
                    link.node1_id not in excluded_nodes and
                    link.node2_id not in excluded_nodes):
                sub_topology.add_link(link)

        return sub_topology

    @staticmethod
    def calculate_path_similarity(path1: PathInfo, path2: PathInfo) -> float:
        """
        计算两条路径的相似度

        Args:
            path1: 路径1
            path2: 路径2

        Returns:
            float: 相似度 [0, 1]，0表示完全不同，1表示完全相同
        """
        if not path1.nodes or not path2.nodes:
            return 0.0

        # 计算节点重叠度
        nodes1 = set(path1.nodes)
        nodes2 = set(path2.nodes)

        intersection = len(nodes1.intersection(nodes2))
        union = len(nodes1.union(nodes2))

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def get_path_bottleneck_bandwidth(topology: NetworkTopology, path: PathInfo) -> float:
        """获取路径的瓶颈带宽"""
        if not path.links:
            return float('inf')

        min_bandwidth = float('inf')
        for node1, node2 in path.links:
            link = topology.get_link(node1, node2)
            if link:
                min_bandwidth = min(min_bandwidth, link.available_bandwidth)
            else:
                return 0.0

        return min_bandwidth if min_bandwidth != float('inf') else 0.0

    @staticmethod
    def update_path_utilization(topology: NetworkTopology, path: PathInfo,
                                bandwidth_usage: float):
        """更新路径上所有链路的利用率"""
        for node1, node2 in path.links:
            link = topology.get_link(node1, node2)
            if link and link.bandwidth > 0:
                additional_utilization = bandwidth_usage / link.bandwidth
                link.utilization = min(1.0, link.utilization + additional_utilization)


class PathQualityEvaluator:
    """路径质量评估器"""

    def __init__(self, topology: NetworkTopology):
        self.topology = topology

    def evaluate_path_quality(self, path: PathInfo,
                              weight_delay: float = 0.4,
                              weight_bandwidth: float = 0.3,
                              weight_hops: float = 0.3) -> float:
        """
        评估路径质量

        Args:
            path: 路径信息
            weight_delay: 延迟权重
            weight_bandwidth: 带宽权重
            weight_hops: 跳数权重

        Returns:
            float: 路径质量评分 [0, 1]，越高越好
        """
        if not path.links:
            return 0.0

        # 归一化延迟 (越小越好)
        max_delay = 1000.0  # 假设最大延迟1000ms
        delay_score = max(0, 1 - path.total_delay / max_delay)

        # 归一化带宽 (越大越好)
        max_bandwidth = 10.0  # 假设最大带宽10Gbps
        bandwidth_score = min(1.0, path.bandwidth / max_bandwidth)

        # 归一化跳数 (越小越好)
        max_hops = 20  # 假设最大跳数20
        hops_score = max(0, 1 - path.length / max_hops)

        # 综合评分
        quality_score = (weight_delay * delay_score +
                         weight_bandwidth * bandwidth_score +
                         weight_hops * hops_score)

        return min(1.0, max(0.0, quality_score))

    def rank_paths_by_quality(self, paths: List[PathInfo]) -> List[Tuple[PathInfo, float]]:
        """按质量对路径排序"""
        path_scores = []
        for path in paths:
            score = self.evaluate_path_quality(path)
            path_scores.append((path, score))

        # 按评分降序排序
        path_scores.sort(key=lambda x: x[1], reverse=True)
        return path_scores


class NetworkConnectivityAnalyzer:
    """网络连通性分析器"""

    def __init__(self, topology: NetworkTopology):
        self.topology = topology

    def is_connected(self) -> bool:
        """检查网络是否连通"""
        return nx.is_connected(self.topology.graph)

    def find_articulation_points(self) -> List[str]:
        """查找关键节点（割点）"""
        return list(nx.articulation_points(self.topology.graph))

    def find_bridges(self) -> List[Tuple[str, str]]:
        """查找关键链路（桥）"""
        return list(nx.bridges(self.topology.graph))

    def calculate_node_betweenness(self) -> Dict[str, float]:
        """计算节点中介中心性"""
        return nx.betweenness_centrality(self.topology.graph, weight='weight')

    def calculate_edge_betweenness(self) -> Dict[Tuple[str, str], float]:
        """计算边中介中心性"""
        return nx.edge_betweenness_centrality(self.topology.graph, weight='weight')

    def get_connectivity_statistics(self) -> Dict:
        """获取连通性统计信息"""
        graph = self.topology.graph

        stats = {
            'is_connected': nx.is_connected(graph),
            'num_components': nx.number_connected_components(graph),
            'average_clustering': nx.average_clustering(graph),
            'diameter': 0,
            'average_path_length': 0,
            'articulation_points': len(self.find_articulation_points()),
            'bridges': len(self.find_bridges())
        }

        if stats['is_connected']:
            stats['diameter'] = nx.diameter(graph)
            stats['average_path_length'] = nx.average_shortest_path_length(graph, weight='weight')

        return stats


def test_algorithms():
    """测试算法功能"""
    print("测试基础算法...")

    # 导入依赖
    try:
        from topology_base import Position, NodeType
    except ImportError:
        try:
            from topology.topology_base import Position, NodeType
        except ImportError:
            from ..topology.topology_base import Position, NodeType

    topology = NetworkTopology()

    # 添加节点
    nodes = [
        Node("A", NodeType.SATELLITE, Position(0, 0, 0)),
        Node("B", NodeType.SATELLITE, Position(1, 0, 0)),
        Node("C", NodeType.SATELLITE, Position(2, 0, 0)),
        Node("D", NodeType.SATELLITE, Position(1, 1, 0)),
        Node("E", NodeType.GROUND_STATION, Position(3, 0, 0))
    ]

    for node in nodes:
        topology.add_node(node)

    # 添加链路
    links = [
        Link("A", "B", 10.0, 10.0),
        Link("B", "C", 10.0, 15.0),
        Link("A", "D", 10.0, 12.0),
        Link("D", "C", 10.0, 8.0),
        Link("C", "E", 5.0, 20.0),
        Link("B", "D", 10.0, 5.0)
    ]

    for link in links:
        topology.add_link(link)

    print(f"创建测试拓扑: {topology}")

    # 测试Dijkstra算法
    finder = DijkstraPathFinder(topology)
    path = finder.find_shortest_path("A", "E")

    if path:
        print(f"A到E的最短路径: {path}")
    else:
        print("未找到A到E的路径")

    # 测试K最短路径
    k_paths = finder.find_k_shortest_paths("A", "E", k=3)
    print(f"A到E的3条最短路径:")
    for i, path in enumerate(k_paths):
        print(f"  路径{i + 1}: {path}")

    # 测试链路不相交路径
    disjoint_finder = LinkDisjointPathFinder(topology)
    disjoint_paths = disjoint_finder.find_link_disjoint_paths("A", "E", k=2)
    print(f"A到E的2条链路不相交路径:")
    for i, path in enumerate(disjoint_paths):
        print(f"  路径{i + 1}: {path}")

    # 验证链路不相交
    is_disjoint = disjoint_finder.verify_link_disjoint(disjoint_paths)
    print(f"路径是否链路不相交: {is_disjoint}")

    # 测试路径质量评估
    evaluator = PathQualityEvaluator(topology)
    ranked_paths = evaluator.rank_paths_by_quality(k_paths)
    print(f"按质量排序的路径:")
    for i, (path, score) in enumerate(ranked_paths):
        print(f"  路径{i + 1} (质量={score:.3f}): {path}")

    # 测试连通性分析
    analyzer = NetworkConnectivityAnalyzer(topology)
    connectivity_stats = analyzer.get_connectivity_statistics()
    print(f"网络连通性统计: {connectivity_stats}")

    print("✅ 算法测试完成!")


if __name__ == "__main__":
    test_algorithms()