"""
流量模型实现
基于论文中的流量生成模型，支持人口分布和Pareto流量模式
"""

import numpy as np
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


@dataclass
class TrafficDemand:
    """流量需求类"""
    source_id: str
    destination_id: str
    bandwidth: float  # Mbps
    start_time: float  # 秒
    duration: float  # 秒
    priority: int = 1  # 优先级 (1=highest, 3=lowest)

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

    def is_active_at_time(self, time: float) -> bool:
        """检查在指定时间是否活跃"""
        return self.start_time <= time <= self.end_time

    def __str__(self):
        return f"Flow({self.source_id}->{self.destination_id}, {self.bandwidth:.1f}Mbps, {self.duration:.1f}s)"


class FlowType(Enum):
    """流量类型"""
    ELEPHANT = "elephant"  # 大象流
    MOUSE = "mouse"  # 老鼠流


class PopulationZone:
    """人口分布区域"""

    def __init__(self, zone_id: int, center_lat: float, center_lon: float, population: int):
        self.zone_id = zone_id
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.population = population
        self.traffic_density = 0.0

    def calculate_distance_to(self, other: 'PopulationZone') -> float:
        """计算到另一个区域的距离（简化的球面距离）"""
        R = 6371  # 地球半径 km

        lat1, lon1 = math.radians(self.center_lat), math.radians(self.center_lon)
        lat2, lon2 = math.radians(other.center_lat), math.radians(other.center_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c


class TrafficMatrix:
    """流量矩阵生成器"""

    def __init__(self, alpha: float = 0.5, beta: float = 2.0):
        """
        初始化流量矩阵生成器

        Args:
            alpha: 流量密度指数
            beta: 距离衰减指数
        """
        self.alpha = alpha
        self.beta = beta
        self.population_zones = []
        self.traffic_matrix = {}

    def add_population_zone(self, zone: PopulationZone):
        """添加人口分布区域"""
        self.population_zones.append(zone)

    def generate_default_zones(self, num_zones: int = 15) -> List[PopulationZone]:
        """生成默认的人口分布区域（基于主要城市）"""
        # 主要城市及其人口（百万）
        major_cities = [
            ("Beijing", 39.9042, 116.4074, 21.5),
            ("New_York", 40.7128, -74.0060, 8.4),
            ("London", 51.5074, -0.1278, 9.0),
            ("Tokyo", 35.6762, 139.6503, 13.9),
            ("Sydney", -33.8688, 151.2093, 5.3),
            ("Moscow", 55.7558, 37.6173, 12.5),
            ("Cairo", 30.0444, 31.2357, 10.2),
            ("Sao_Paulo", -23.5505, -46.6333, 12.3),
            ("Mumbai", 19.0760, 72.8777, 20.4),
            ("Lagos", 6.5244, 3.3792, 14.8),
            ("Berlin", 52.5200, 13.4050, 3.7),
            ("Toronto", 43.6532, -79.3832, 6.2),
            ("Dubai", 25.2048, 55.2708, 3.4),
            ("Singapore", 1.3521, 103.8198, 5.9),
            ("Mexico_City", 19.4326, -99.1332, 9.2)
        ]

        zones = []
        for i, (name, lat, lon, pop) in enumerate(major_cities[:num_zones]):
            zone = PopulationZone(i, lat, lon, int(pop * 1000000))  # 转换为人数
            zones.append(zone)

        return zones

    def calculate_traffic_matrix(self, total_traffic: float = 100.0) -> Dict[Tuple[int, int], float]:
        """
        计算流量矩阵

        Args:
            total_traffic: 总流量 (Gbps)

        Returns:
            Dict[Tuple[int, int], float]: (源区域, 目标区域) -> 流量需求
        """
        if not self.population_zones:
            self.population_zones = self.generate_default_zones()

        traffic_matrix = {}
        total_demand = 0.0

        # 计算原始流量需求矩阵
        for i, zone_a in enumerate(self.population_zones):
            for j, zone_b in enumerate(self.population_zones):
                if i != j:
                    # 基于论文公式 (1): TMa,b = (UDa · UDb)^α / l^β_a,b
                    distance = zone_a.calculate_distance_to(zone_b)
                    if distance > 0:
                        demand = (zone_a.population * zone_b.population) ** self.alpha / (distance ** self.beta)
                        traffic_matrix[(i, j)] = demand
                        total_demand += demand

        # 归一化并应用总流量
        normalized_matrix = {}
        for (i, j), demand in traffic_matrix.items():
            normalized_demand = total_traffic * (demand / total_demand)
            normalized_matrix[(i, j)] = normalized_demand

        self.traffic_matrix = normalized_matrix
        return normalized_matrix

    def get_flow_between_zones(self, zone_a_id: int, zone_b_id: int) -> float:
        """获取两个区域间的流量需求"""
        return self.traffic_matrix.get((zone_a_id, zone_b_id), 0.0)


class ParetoFlowGenerator:
    """Pareto分布流量生成器"""

    def __init__(self, shape_on: float = 1.5, scale_on: float = 500,
                 shape_off: float = 1.5, scale_off: float = 1000):
        """
        初始化Pareto流量生成器

        Args:
            shape_on: on-time的形状参数
            scale_on: on-time的尺度参数 (ms)
            shape_off: off-time的形状参数
            scale_off: off-time的尺度参数 (ms)
        """
        self.shape_on = shape_on
        self.scale_on = scale_on
        self.shape_off = shape_off
        self.scale_off = scale_off

    def generate_pareto_sample(self, shape: float, scale: float) -> float:
        """生成Pareto分布样本"""
        u = random.random()
        return scale * ((1 - u) ** (-1 / shape) - 1)

    def generate_on_time(self) -> float:
        """生成on-time持续时间 (秒)"""
        return self.generate_pareto_sample(self.shape_on, self.scale_on) / 1000.0

    def generate_off_time(self) -> float:
        """生成off-time持续时间 (秒)"""
        return self.generate_pareto_sample(self.shape_off, self.scale_off) / 1000.0

    def generate_flow_sequence(self, duration: float,
                               avg_bandwidth: float) -> List[Tuple[float, float, float]]:
        """
        生成流量序列

        Args:
            duration: 总持续时间 (秒)
            avg_bandwidth: 平均带宽 (Mbps)

        Returns:
            List[Tuple[float, float, float]]: [(开始时间, 持续时间, 带宽), ...]
        """
        flows = []
        current_time = 0.0

        while current_time < duration:
            # 生成off-time
            off_time = self.generate_off_time()
            current_time += off_time

            if current_time >= duration:
                break

            # 生成on-time和带宽
            on_time = self.generate_on_time()
            # 带宽在平均值附近变化
            bandwidth = avg_bandwidth * random.uniform(0.5, 1.5)

            if current_time + on_time <= duration:
                flows.append((current_time, on_time, bandwidth))

            current_time += on_time

        return flows


class TrafficGenerator:
    """综合流量生成器"""

    def __init__(self, gs_zone_mapping: Dict[str, int] = None):
        """
        初始化流量生成器

        Args:
            gs_zone_mapping: 地面站ID到区域ID的映射
        """
        self.traffic_matrix = TrafficMatrix()
        self.pareto_generator = ParetoFlowGenerator()
        self.gs_zone_mapping = gs_zone_mapping or {}
        self.elephant_threshold = 50.0  # Mbps，超过此值的流量为大象流

    def setup_default_mapping(self, ground_station_ids: List[str], num_zones: int = None):
        """设置默认的地面站到区域映射"""
        if num_zones is None:
            num_zones = len(ground_station_ids)

        zones = self.traffic_matrix.generate_default_zones(num_zones)
        self.traffic_matrix.population_zones = zones

        # 简单映射：第i个地面站对应第i个区域
        for i, gs_id in enumerate(ground_station_ids):
            if i < len(zones):
                self.gs_zone_mapping[gs_id] = zones[i].zone_id

    def classify_flow_type(self, bandwidth: float) -> FlowType:
        """分类流量类型"""
        return FlowType.ELEPHANT if bandwidth >= self.elephant_threshold else FlowType.MOUSE

    def generate_traffic_demands(self, ground_station_ids: List[str],
                                 total_traffic: float = 8.0,  # Gbps
                                 duration: float = 300.0,  # 秒
                                 elephant_ratio: float = 0.3) -> List[TrafficDemand]:
        """
        生成流量需求

        Args:
            ground_station_ids: 地面站ID列表
            total_traffic: 总流量 (Gbps)
            duration: 仿真持续时间 (秒)
            elephant_ratio: 大象流的比例

        Returns:
            List[TrafficDemand]: 流量需求列表
        """
        if not self.gs_zone_mapping:
            self.setup_default_mapping(ground_station_ids)

        # 计算流量矩阵
        traffic_matrix = self.traffic_matrix.calculate_traffic_matrix(total_traffic)

        demands = []

        # 为每对地面站生成流量
        for i, source_gs in enumerate(ground_station_ids):
            for j, dest_gs in enumerate(ground_station_ids):
                if i != j:
                    source_zone = self.gs_zone_mapping.get(source_gs, i)
                    dest_zone = self.gs_zone_mapping.get(dest_gs, j)

                    # 获取区域间的平均流量需求
                    avg_demand = traffic_matrix.get((source_zone, dest_zone), 0)

                    if avg_demand > 0:
                        # 转换为Mbps
                        avg_bandwidth = avg_demand * 1000  # Gbps -> Mbps

                        # 生成流量序列
                        flow_sequence = self.pareto_generator.generate_flow_sequence(
                            duration, avg_bandwidth / 10)  # 分散到多个小流

                        # 创建流量需求
                        for start_time, flow_duration, bandwidth in flow_sequence:
                            flow_type = self.classify_flow_type(bandwidth)

                            # 根据大象流比例调整
                            if flow_type == FlowType.ELEPHANT:
                                bandwidth *= (1 + elephant_ratio)
                                priority = 1  # 高优先级
                            else:
                                priority = 2  # 中等优先级

                            demand = TrafficDemand(
                                source_id=source_gs,
                                destination_id=dest_gs,
                                bandwidth=bandwidth,
                                start_time=start_time,
                                duration=flow_duration,
                                priority=priority
                            )
                            demands.append(demand)

        # 按带宽降序排序（大象流优先）
        demands.sort(key=lambda x: x.bandwidth, reverse=True)

        return demands

    def get_active_demands_at_time(self, demands: List[TrafficDemand],
                                   time: float) -> List[TrafficDemand]:
        """获取指定时间的活跃流量需求"""
        return [demand for demand in demands if demand.is_active_at_time(time)]

    def get_flow_statistics(self, demands: List[TrafficDemand]) -> Dict:
        """获取流量统计信息"""
        if not demands:
            return {}

        bandwidths = [d.bandwidth for d in demands]
        durations = [d.duration for d in demands]

        elephant_flows = [d for d in demands if self.classify_flow_type(d.bandwidth) == FlowType.ELEPHANT]
        mouse_flows = [d for d in demands if self.classify_flow_type(d.bandwidth) == FlowType.MOUSE]

        return {
            'total_flows': len(demands),
            'elephant_flows': len(elephant_flows),
            'mouse_flows': len(mouse_flows),
            'avg_bandwidth': np.mean(bandwidths),
            'max_bandwidth': np.max(bandwidths),
            'min_bandwidth': np.min(bandwidths),
            'avg_duration': np.mean(durations),
            'total_traffic': sum(d.bandwidth * d.duration / 1000 for d in demands),  # Gb·s
            'elephant_ratio': len(elephant_flows) / len(demands) if demands else 0
        }


def create_test_traffic(ground_station_ids: List[str] = None) -> List[TrafficDemand]:
    """创建测试流量"""
    if ground_station_ids is None:
        ground_station_ids = [f"GS_{i}" for i in range(15)]

    generator = TrafficGenerator()
    demands = generator.generate_traffic_demands(
        ground_station_ids=ground_station_ids,
        total_traffic=8.0,  # 8 Gbps
        duration=300.0,  # 5分钟
        elephant_ratio=0.3
    )

    return demands


def main():
    """测试函数"""
    print("生成流量需求...")

    # 创建地面站列表
    ground_stations = [f"GS_{i}" for i in range(15)]

    # 生成流量
    generator = TrafficGenerator()
    demands = generator.generate_traffic_demands(
        ground_station_ids=ground_stations,
        total_traffic=8.0,
        duration=300.0
    )

    # 统计信息
    stats = generator.get_flow_statistics(demands)
    print(f"流量统计: {stats}")

    # 显示前几个流量需求
    print(f"\n前10个流量需求:")
    for i, demand in enumerate(demands[:10]):
        print(f"  {i + 1}: {demand}")

    # 测试时间片流量
    print(f"\n时间0-60s的活跃流量:")
    active_flows = generator.get_active_demands_at_time(demands, 30.0)
    print(f"  活跃流量数: {len(active_flows)}")
    print(f"  总带宽: {sum(f.bandwidth for f in active_flows):.1f} Mbps")

    print("\n✅ 流量生成完成!")


if __name__ == "__main__":
    main()