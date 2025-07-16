"""
LEO卫星星座建模
实现GlobalStar和Iridium星座的拓扑生成
"""

import numpy as np
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from .topology_base import NetworkTopology, Node, Link, Position, NodeType, TopologyManager


@dataclass
class ConstellationConfig:
    """星座配置参数"""
    name: str
    num_satellites: int
    altitude: float  # km
    inclination: float  # degrees
    num_planes: int
    sats_per_plane: int
    inter_plane_links: bool = True
    intra_plane_links: bool = True


class SatelliteConstellation:
    """卫星星座类"""

    # 预定义的星座配置
    CONFIGS = {
        'globalstar': ConstellationConfig(
            name='GlobalStar',
            num_satellites=48,
            altitude=1400,
            inclination=55.0,
            num_planes=8,
            sats_per_plane=6,
            inter_plane_links=True,
            intra_plane_links=True
        ),
        'iridium': ConstellationConfig(
            name='Iridium',
            num_satellites=66,
            altitude=780,
            inclination=90.0,
            num_planes=6,
            sats_per_plane=11,
            inter_plane_links=True,
            intra_plane_links=True
        )
    }

    def __init__(self, config_name: str = 'globalstar'):
        if config_name not in self.CONFIGS:
            raise ValueError(f"Unknown constellation: {config_name}")

        self.config = self.CONFIGS[config_name]
        self.earth_radius = 6371.0  # km

    def calculate_satellite_position(self, plane_idx: int, sat_idx: int, time: float = 0) -> Position:
        """计算卫星在指定时间的位置"""
        config = self.config

        # 轨道半径
        orbit_radius = self.earth_radius + config.altitude

        # 轨道周期（秒）
        orbital_period = 2 * math.pi * math.sqrt(orbit_radius ** 3 / 398600.4418)

        # 平面间角度间隔
        plane_angle = 2 * math.pi * plane_idx / config.num_planes

        # 卫星在轨道平面内的角度
        sat_angle = 2 * math.pi * sat_idx / config.sats_per_plane

        # 考虑时间的轨道运动
        time_angle = 2 * math.pi * time / orbital_period
        sat_angle += time_angle

        # 倾斜角转换为弧度
        inclination_rad = math.radians(config.inclination)

        # 计算3D坐标
        x = orbit_radius * (math.cos(sat_angle) * math.cos(plane_angle) -
                            math.sin(sat_angle) * math.sin(plane_angle) * math.cos(inclination_rad))
        y = orbit_radius * (math.cos(sat_angle) * math.sin(plane_angle) +
                            math.sin(sat_angle) * math.cos(plane_angle) * math.cos(inclination_rad))
        z = orbit_radius * math.sin(sat_angle) * math.sin(inclination_rad)

        return Position(x, y, z)

    def generate_satellite_nodes(self, time: float = 0) -> List[Node]:
        """生成所有卫星节点"""
        satellites = []
        config = self.config

        for plane_idx in range(config.num_planes):
            for sat_idx in range(config.sats_per_plane):
                # 卫星ID
                sat_id = f"S_{plane_idx}_{sat_idx}"

                # 计算位置
                position = self.calculate_satellite_position(plane_idx, sat_idx, time)

                # 创建卫星节点
                satellite = Node(sat_id, NodeType.SATELLITE, position)
                satellite.attributes = {
                    'plane_idx': plane_idx,
                    'sat_idx': sat_idx,
                    'altitude': config.altitude,
                    'inclination': config.inclination
                }

                satellites.append(satellite)

        return satellites

    def calculate_link_delay(self, pos1: Position, pos2: Position) -> float:
        """计算链路传播延迟（ms）"""
        distance = pos1.distance_to(pos2)  # km
        speed_of_light = 299792.458  # km/ms
        return distance / speed_of_light

    def should_create_link(self, sat1: Node, sat2: Node, max_distance: float = 8000) -> bool:
        """判断两颗卫星是否应该建立链路"""
        if sat1.position is None or sat2.position is None:
            return False

        distance = sat1.position.distance_to(sat2.position)

        # 距离限制
        if distance > max_distance:
            return False

        plane1 = sat1.attributes['plane_idx']
        plane2 = sat2.attributes['plane_idx']
        sat_idx1 = sat1.attributes['sat_idx']
        sat_idx2 = sat2.attributes['sat_idx']

        # 同轨道平面内相邻卫星
        if plane1 == plane2:
            sats_per_plane = self.config.sats_per_plane
            if (abs(sat_idx1 - sat_idx2) == 1 or
                    abs(sat_idx1 - sat_idx2) == sats_per_plane - 1):
                return self.config.intra_plane_links

        # 不同轨道平面间的卫星
        elif abs(plane1 - plane2) == 1 or abs(plane1 - plane2) == self.config.num_planes - 1:
            # 只连接同一轨道位置的卫星
            if sat_idx1 == sat_idx2:
                return self.config.inter_plane_links

        return False

    def generate_satellite_links(self, satellites: List[Node], bandwidth: float = 10.0) -> List[Link]:
        """生成卫星间链路"""
        links = []

        for i, sat1 in enumerate(satellites):
            for j, sat2 in enumerate(satellites[i + 1:], i + 1):
                if self.should_create_link(sat1, sat2):
                    delay = self.calculate_link_delay(sat1.position, sat2.position)
                    link = Link(sat1.id, sat2.id, bandwidth, delay)
                    links.append(link)

        return links

    def generate_topology(self, time: float = 0, bandwidth: float = 10.0) -> NetworkTopology:
        """生成完整的卫星网络拓扑"""
        topology = NetworkTopology()

        # 生成卫星节点
        satellites = self.generate_satellite_nodes(time)
        for satellite in satellites:
            topology.add_node(satellite)

        # 生成卫星间链路
        links = self.generate_satellite_links(satellites, bandwidth)
        for link in links:
            topology.add_link(link)

        return topology


class GroundStationManager:
    """地面站管理器"""

    def __init__(self):
        # 主要城市的地面站（经纬度）
        self.major_cities = {
            'Beijing': (39.9042, 116.4074),
            'New_York': (40.7128, -74.0060),
            'London': (51.5074, -0.1278),
            'Tokyo': (35.6762, 139.6503),
            'Sydney': (-33.8688, 151.2093),
            'Moscow': (55.7558, 37.6173),
            'Cairo': (30.0444, 31.2357),
            'Sao_Paulo': (-23.5505, -46.6333),
            'Mumbai': (19.0760, 72.8777),
            'Lagos': (6.5244, 3.3792),
            'Berlin': (52.5200, 13.4050),
            'Toronto': (43.6532, -79.3832),
            'Dubai': (25.2048, 55.2708),
            'Singapore': (1.3521, 103.8198),
            'Mexico_City': (19.4326, -99.1332)
        }

    def lat_lon_to_cartesian(self, lat: float, lon: float, altitude: float = 0) -> Position:
        """将经纬度转换为笛卡尔坐标"""
        earth_radius = 6371.0  # km
        radius = earth_radius + altitude

        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        x = radius * math.cos(lat_rad) * math.cos(lon_rad)
        y = radius * math.cos(lat_rad) * math.sin(lon_rad)
        z = radius * math.sin(lat_rad)

        return Position(x, y, z)

    def generate_ground_stations(self, num_stations: int = None) -> List[Node]:
        """生成地面站节点"""
        if num_stations is None:
            cities_to_use = list(self.major_cities.items())
        else:
            cities_to_use = list(self.major_cities.items())[:num_stations]

        ground_stations = []

        for i, (city_name, (lat, lon)) in enumerate(cities_to_use):
            gs_id = f"GS_{i}"
            position = self.lat_lon_to_cartesian(lat, lon)

            gs = Node(gs_id, NodeType.GROUND_STATION, position)
            gs.attributes = {
                'city': city_name,
                'latitude': lat,
                'longitude': lon,
                'index': i
            }

            ground_stations.append(gs)

        return ground_stations

    def find_visible_satellites(self, ground_station: Node, satellites: List[Node],
                                elevation_angle: float = 0.0, max_distance: float = 5000) -> List[Node]:
        """找到对地面站可见的卫星"""
        if ground_station.position is None:
            return []

        visible_satellites = []
        min_elevation_rad = math.radians(elevation_angle)
        earth_radius = 6371.0

        for satellite in satellites:
            if satellite.position is None:
                continue

            # 计算距离
            distance = ground_station.position.distance_to(satellite.position)
            if distance > max_distance:
                continue

            # 计算仰角
            gs_to_sat = np.array([
                satellite.position.x - ground_station.position.x,
                satellite.position.y - ground_station.position.y,
                satellite.position.z - ground_station.position.z
            ])

            gs_position_vector = np.array([
                ground_station.position.x,
                ground_station.position.y,
                ground_station.position.z
            ])

            # 地面站到卫星的向量与地心到地面站向量的夹角
            dot_product = np.dot(gs_to_sat, gs_position_vector)
            magnitude_product = np.linalg.norm(gs_to_sat) * np.linalg.norm(gs_position_vector)

            if magnitude_product > 0:
                cos_angle = dot_product / magnitude_product
                angle = math.acos(np.clip(cos_angle, -1, 1))
                elevation = math.pi / 2 - angle

                if elevation >= min_elevation_rad:
                    visible_satellites.append(satellite)

        return visible_satellites

    def generate_ground_links(self, ground_stations: List[Node], satellites: List[Node],
                              bandwidth: float = 5.0) -> List[Link]:
        """生成地面站到卫星的链路"""
        links = []

        for gs in ground_stations:
            visible_sats = self.find_visible_satellites(gs, satellites)

            # 连接到最近的2-3个可见卫星（提高连通性）
            if visible_sats:
                # 按距离排序，连接最近的几个
                visible_sats.sort(key=lambda s: gs.position.distance_to(s.position))
                
                # 连接到最近的2个卫星（或所有可见卫星，如果少于2个）
                num_connections = min(2, len(visible_sats))
                
                for i in range(num_connections):
                    sat = visible_sats[i]
                    distance = gs.position.distance_to(sat.position)
                    delay = distance / 299792.458  # km/ms

                    link = Link(gs.id, sat.id, bandwidth, delay)
                    links.append(link)

        return links


class LEONetworkBuilder:
    """LEO网络构建器"""

    def __init__(self, constellation_type: str = 'globalstar', num_ground_stations: int = 15):
        self.constellation = SatelliteConstellation(constellation_type)
        self.gs_manager = GroundStationManager()
        self.num_ground_stations = num_ground_stations

    def build_network(self, time: float = 0, satellite_bandwidth: float = 10.0,
                      ground_bandwidth: float = 5.0) -> NetworkTopology:
        """构建完整的LEO网络"""
        topology = NetworkTopology()

        # 生成卫星网络
        satellite_topology = self.constellation.generate_topology(time, satellite_bandwidth)

        # 添加卫星节点和链路
        for node in satellite_topology.nodes.values():
            topology.add_node(node)
        for link in satellite_topology.links.values():
            topology.add_link(link)

        # 生成地面站
        ground_stations = self.gs_manager.generate_ground_stations(self.num_ground_stations)
        for gs in ground_stations:
            topology.add_node(gs)

        # 生成地面站链路
        satellites = [node for node in topology.nodes.values()
                      if node.type == NodeType.SATELLITE]
        ground_links = self.gs_manager.generate_ground_links(
            ground_stations, satellites, ground_bandwidth)

        for link in ground_links:
            topology.add_link(link)

        return topology

    def build_time_series(self, duration: float = 600, time_step: float = 60,
                          satellite_bandwidth: float = 10.0,
                          ground_bandwidth: float = 5.0) -> TopologyManager:
        """构建时间序列拓扑"""
        manager = TopologyManager(time_step)

        current_time = 0
        while current_time < duration:
            topology = self.build_network(current_time, satellite_bandwidth, ground_bandwidth)
            manager.add_snapshot(topology, current_time)
            current_time += time_step

        return manager


def create_test_topology() -> NetworkTopology:
    """创建用于测试的简单拓扑"""
    builder = LEONetworkBuilder('globalstar', 15)
    return builder.build_network()


def main():
    """测试函数"""
    print("创建LEO网络拓扑...")

    # 创建GlobalStar网络
    builder = LEONetworkBuilder('globalstar', 15)
    topology = builder.build_network()

    stats = topology.get_statistics()
    print(f"网络统计: {stats}")

    # 创建时间序列拓扑
    print("\n创建时间序列拓扑...")
    manager = builder.build_time_series(duration=300, time_step=60)

    manager_stats = manager.get_statistics()
    print(f"拓扑管理器统计: {manager_stats}")

    # 测试拓扑变化
    print("\n测试拓扑变化:")
    for i in range(min(3, len(manager.snapshots))):
        snapshot = manager.snapshots[i]
        print(f"  快照 {i}: {snapshot}")

    print("\n✅ LEO网络拓扑创建完成!")


if __name__ == "__main__":
    main()