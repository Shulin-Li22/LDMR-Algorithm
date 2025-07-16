"""
LDMR算法基础数据结构
实现节点、链路和网络拓扑的基础类
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time


class NodeType(Enum):
    """节点类型枚举"""
    SATELLITE = "satellite"
    GROUND_STATION = "ground_station"


@dataclass
class Position:
    """3D位置坐标"""
    x: float
    y: float
    z: float

    def distance_to(self, other: 'Position') -> float:
        """计算到另一个位置的距离"""
        return np.sqrt((self.x - other.x) ** 2 +
                       (self.y - other.y) ** 2 +
                       (self.z - other.z) ** 2)


class Node:
    """网络节点类"""

    def __init__(self, node_id: str, node_type: NodeType, position: Optional[Position] = None):
        self.id = node_id
        self.type = node_type
        self.position = position
        self.neighbors: Set[str] = set()  # 邻居节点ID集合
        self.attributes = {}  # 附加属性

    def add_neighbor(self, neighbor_id: str):
        """添加邻居节点"""
        self.neighbors.add(neighbor_id)

    def remove_neighbor(self, neighbor_id: str):
        """移除邻居节点"""
        self.neighbors.discard(neighbor_id)

    def __str__(self):
        return f"Node({self.id}, {self.type.value})"

    def __repr__(self):
        return self.__str__()


class Link:
    """网络链路类"""

    def __init__(self, node1_id: str, node2_id: str,
                 bandwidth: float = 10.0, delay: float = 0.0):
        # 确保链路的唯一表示（较小ID在前）
        if node1_id <= node2_id:
            self.node1_id = node1_id
            self.node2_id = node2_id
        else:
            self.node1_id = node2_id
            self.node2_id = node1_id

        self.bandwidth = bandwidth  # Gbps
        self.delay = delay  # ms
        self.utilization = 0.0  # 当前利用率 [0,1]
        self.weight = delay  # 动态权重
        self.usage_count = 0  # 使用次数计数
        self.is_active = True  # 是否激活

    @property
    def id(self) -> Tuple[str, str]:
        """链路ID（元组形式）"""
        return (self.node1_id, self.node2_id)

    @property
    def available_bandwidth(self) -> float:
        """可用带宽"""
        return self.bandwidth * (1 - self.utilization)

    def update_weight(self, new_weight: float):
        """更新链路权重"""
        self.weight = new_weight

    def increment_usage(self):
        """增加使用计数"""
        self.usage_count += 1

    def reset_usage(self):
        """重置使用计数"""
        self.usage_count = 0

    def __str__(self):
        return f"Link({self.node1_id}-{self.node2_id}, delay={self.delay:.2f}ms, bw={self.bandwidth}Gbps)"

    def __repr__(self):
        return self.__str__()


class NetworkTopology:
    """网络拓扑类"""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[Tuple[str, str], Link] = {}
        self.graph = nx.Graph()  # NetworkX图对象
        self._adjacency_matrix = None
        self._weight_matrix = None

    def add_node(self, node: Node):
        """添加节点"""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, node_type=node.type, position=node.position)
        self._invalidate_matrices()

    def add_link(self, link: Link):
        """添加链路"""
        if link.node1_id not in self.nodes or link.node2_id not in self.nodes:
            raise ValueError(f"Cannot add link {link.id}: one or both nodes do not exist")

        self.links[link.id] = link
        self.graph.add_edge(link.node1_id, link.node2_id,
                            weight=link.weight, delay=link.delay,
                            bandwidth=link.bandwidth, link_obj=link)

        # 更新节点的邻居关系
        self.nodes[link.node1_id].add_neighbor(link.node2_id)
        self.nodes[link.node2_id].add_neighbor(link.node1_id)
        self._invalidate_matrices()

    def remove_link(self, node1_id: str, node2_id: str):
        """移除链路"""
        link_id = (min(node1_id, node2_id), max(node1_id, node2_id))

        if link_id in self.links:
            del self.links[link_id]

        if self.graph.has_edge(node1_id, node2_id):
            self.graph.remove_edge(node1_id, node2_id)

        # 更新节点的邻居关系
        if node1_id in self.nodes:
            self.nodes[node1_id].remove_neighbor(node2_id)
        if node2_id in self.nodes:
            self.nodes[node2_id].remove_neighbor(node1_id)

        self._invalidate_matrices()

    def get_link(self, node1_id: str, node2_id: str) -> Optional[Link]:
        """获取链路对象"""
        link_id = (min(node1_id, node2_id), max(node1_id, node2_id))
        return self.links.get(link_id)

    def has_link(self, node1_id: str, node2_id: str) -> bool:
        """检查是否存在链路"""
        return self.get_link(node1_id, node2_id) is not None

    def get_neighbors(self, node_id: str) -> List[str]:
        """获取节点的邻居"""
        if node_id in self.nodes:
            return list(self.nodes[node_id].neighbors)
        return []

    def _invalidate_matrices(self):
        """使缓存的矩阵失效"""
        self._adjacency_matrix = None
        self._weight_matrix = None

    def get_adjacency_matrix(self) -> np.ndarray:
        """获取邻接矩阵"""
        if self._adjacency_matrix is None:
            node_list = list(self.nodes.keys())
            size = len(node_list)
            self._adjacency_matrix = np.zeros((size, size))

            for i, node1 in enumerate(node_list):
                for j, node2 in enumerate(node_list):
                    if i != j and self.has_link(node1, node2):
                        self._adjacency_matrix[i][j] = 1

        return self._adjacency_matrix.copy()

    def get_weight_matrix(self) -> np.ndarray:
        """获取权重矩阵"""
        if self._weight_matrix is None:
            node_list = list(self.nodes.keys())
            size = len(node_list)
            self._weight_matrix = np.full((size, size), np.inf)

            # 对角线设为0
            np.fill_diagonal(self._weight_matrix, 0)

            for i, node1 in enumerate(node_list):
                for j, node2 in enumerate(node_list):
                    if i != j:
                        link = self.get_link(node1, node2)
                        if link and link.is_active:
                            self._weight_matrix[i][j] = link.weight

        return self._weight_matrix.copy()

    def update_link_weights(self, weight_updates: Dict[Tuple[str, str], float]):
        """批量更新链路权重"""
        for link_id, new_weight in weight_updates.items():
            if link_id in self.links:
                self.links[link_id].update_weight(new_weight)
                # 同时更新NetworkX图
                node1, node2 = link_id
                if self.graph.has_edge(node1, node2):
                    self.graph[node1][node2]['weight'] = new_weight

        self._invalidate_matrices()

    def reset_link_usage(self):
        """重置所有链路的使用计数"""
        for link in self.links.values():
            link.reset_usage()

    def get_statistics(self) -> Dict:
        """获取拓扑统计信息"""
        satellites = [n for n in self.nodes.values() if n.type == NodeType.SATELLITE]
        ground_stations = [n for n in self.nodes.values() if n.type == NodeType.GROUND_STATION]

        return {
            'total_nodes': len(self.nodes),
            'satellites': len(satellites),
            'ground_stations': len(ground_stations),
            'total_links': len(self.links),
            'average_degree': 2 * len(self.links) / len(self.nodes) if self.nodes else 0,
            'is_connected': nx.is_connected(self.graph) if self.nodes else False
        }

    def copy(self) -> 'NetworkTopology':
        """创建拓扑的深拷贝"""
        new_topology = NetworkTopology()

        # 复制节点
        for node in self.nodes.values():
            new_node = Node(node.id, node.type, node.position)
            new_node.attributes = node.attributes.copy()
            new_topology.add_node(new_node)

        # 复制链路
        for link in self.links.values():
            new_link = Link(link.node1_id, link.node2_id, link.bandwidth, link.delay)
            new_link.weight = link.weight
            new_link.utilization = link.utilization
            new_link.usage_count = link.usage_count
            new_link.is_active = link.is_active
            new_topology.add_link(new_link)

        return new_topology

    def __str__(self):
        stats = self.get_statistics()
        return f"NetworkTopology(nodes={stats['total_nodes']}, links={stats['total_links']})"

    def __repr__(self):
        return self.__str__()


class TopologySnapshot:
    """拓扑快照类"""

    def __init__(self, timestamp: float, duration: float, topology: NetworkTopology):
        self.timestamp = timestamp
        self.duration = duration
        self.topology = topology
        self.active_links: Set[Tuple[str, str]] = set()
        self.metadata = {}

        # 初始化活跃链路集合
        self.update_active_links()

    def update_active_links(self):
        """更新活跃链路集合"""
        self.active_links = {link.id for link in self.topology.links.values() if link.is_active}

    def get_end_time(self) -> float:
        """获取快照结束时间"""
        return self.timestamp + self.duration

    def __str__(self):
        return f"TopologySnapshot(t={self.timestamp:.2f}s, duration={self.duration:.2f}s, links={len(self.active_links)})"


class TopologyManager:
    """拓扑管理器"""

    def __init__(self, snapshot_duration: float = 60.0):
        self.snapshot_duration = snapshot_duration
        self.snapshots: List[TopologySnapshot] = []
        self.current_index = 0

    def add_snapshot(self, topology: NetworkTopology, timestamp: float = None) -> TopologySnapshot:
        """添加拓扑快照"""
        if timestamp is None:
            timestamp = len(self.snapshots) * self.snapshot_duration

        snapshot = TopologySnapshot(timestamp, self.snapshot_duration, topology.copy())
        self.snapshots.append(snapshot)
        return snapshot

    def get_snapshot_at_time(self, time: float) -> Optional[TopologySnapshot]:
        """获取指定时间的拓扑快照"""
        for snapshot in self.snapshots:
            if snapshot.timestamp <= time <= snapshot.get_end_time():
                return snapshot
        return None

    def get_current_snapshot(self) -> Optional[TopologySnapshot]:
        """获取当前快照"""
        if 0 <= self.current_index < len(self.snapshots):
            return self.snapshots[self.current_index]
        return None

    def next_snapshot(self) -> Optional[TopologySnapshot]:
        """切换到下一个快照"""
        if self.current_index < len(self.snapshots) - 1:
            self.current_index += 1
            return self.get_current_snapshot()
        return None

    def reset(self):
        """重置到第一个快照"""
        self.current_index = 0

    def get_statistics(self) -> Dict:
        """获取管理器统计信息"""
        return {
            'total_snapshots': len(self.snapshots),
            'current_index': self.current_index,
            'snapshot_duration': self.snapshot_duration,
            'total_duration': len(self.snapshots) * self.snapshot_duration
        }