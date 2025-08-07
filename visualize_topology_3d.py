#!/usr/bin/env python3
"""
3D网络拓扑可视化工具
作者：Gemini
描述：此脚本用于生成并以3D形式可视化LEO卫星网络的初始拓扑图，并会绘制地球作为参照。
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# --- 关键步骤 1: 添加项目路径，确保可以正确导入模块 ---
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

try:
    # --- 关键步骤 2: 导入项目中的核心类 ---
    from topology.satellite_constellation import LEONetworkBuilder, GroundStationManager
    from topology.topology_base import NodeType
except ImportError as e:
    print("错误：无法导入项目模块。")
    print(f"请确保此脚本位于 'ldmr-algorithm' 项目的根目录下，并且 'src' 目录存在。")
    print(f"详细错误: {e}")
    sys.exit(1)


def visualize_topology_3d(constellation_type: str = 'globalstar', num_ground_stations: int = 15):
    """
    生成并以3D形式可视化一个LEO卫星网络的拓扑图。

    Args:
        constellation_type (str): 星座类型, 'globalstar' 或 'iridium'。
        num_ground_stations (int): 地面站的数量。
    """
    print(f"🚀 开始生成 '{constellation_type}' 星座的3D拓扑...")

    # --- 关键步骤 3: 使用LEONetworkBuilder构建网络 ---
    builder = LEONetworkBuilder(constellation_type, num_ground_stations)
    topology = builder.build_network(time=0)  # 使用时间点 t=0

    stats = topology.get_statistics()
    print(f"✅ 拓扑生成完毕: {stats['total_nodes']} 个节点, {stats['total_links']} 条链路。")
    print("🎨 开始进行3D可视化...")

    # --- 关键步骤 4: 创建3D绘图环境 ---
    fig = plt.figure(figsize=(20, 18))
    ax = fig.add_subplot(111, projection='3d')

    # --- 关键步骤 5: 绘制地球作为参考 ---
    # 从GroundStationManager获取地球半径的定义
    earth_radius = GroundStationManager().lat_lon_to_cartesian(0, 0).x  # 简便方法获取半径
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = earth_radius * np.outer(np.cos(u), np.sin(v))
    y = earth_radius * np.outer(np.sin(u), np.sin(v))
    z = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(x, y, z, color='lightblue', alpha=0.3, rstride=5, cstride=5)

    # --- 关键步骤 6: 提取节点3D坐标并分类 ---
    nodes = topology.nodes.values()
    satellite_nodes = [node for node in nodes if node.type == NodeType.SATELLITE]
    ground_station_nodes = [node for node in nodes if node.type == NodeType.GROUND_STATION]

    # --- 关键步骤 7: 在3D空间中绘制节点和链路 ---
    # 绘制卫星节点
    sat_x = [node.position.x for node in satellite_nodes]
    sat_y = [node.position.y for node in satellite_nodes]
    sat_z = [node.position.z for node in satellite_nodes]
    ax.scatter(sat_x, sat_y, sat_z, c='#2E86AB', marker='o', s=30, label='Satellite')

    # 绘制地面站节点
    gs_x = [node.position.x for node in ground_station_nodes]
    gs_y = [node.position.y for node in ground_station_nodes]
    gs_z = [node.position.z for node in ground_station_nodes]
    ax.scatter(gs_x, gs_y, gs_z, c='#A23B72', marker='s', s=50, label='Ground Station')

    # 绘制链路
    for link in topology.links.values():
        node1 = topology.nodes[link.node1_id]
        node2 = topology.nodes[link.node2_id]
        x_coords = [node1.position.x, node2.position.x]
        y_coords = [node1.position.y, node2.position.y]
        z_coords = [node1.position.z, node2.position.z]
        ax.plot(x_coords, y_coords, z_coords, color='#a0a0a0', linewidth=0.5, alpha=0.7)

    # --- 关键步骤 8: 美化图表并显示 ---
    ax.set_title(f'{constellation_type.capitalize()} Constellation Network Topology (3D)', fontsize=20, fontweight='bold')
    ax.set_xlabel('X (km)', fontsize=12)
    ax.set_ylabel('Y (km)', fontsize=12)
    ax.set_zlabel('Z (km)', fontsize=12)
    ax.legend(loc='upper right', fontsize=12)

    # 设置坐标轴范围以确保视图美观
    max_range = np.array([sat_x, sat_y, sat_z]).max() * 1.1
    ax.set_xlim([-max_range, max_range])
    ax.set_ylim([-max_range, max_range])
    ax.set_zlim([-max_range, max_range])

    # 设置一个合适的视角
    ax.view_init(elev=40., azim=45)

    # 保存图像
    output_dir = project_root / 'results' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'{constellation_type}_topology_3d.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    print(f"✅ 3D可视化图表已保存至: {output_path}")

    plt.show()


if __name__ == '__main__':
    # 您可以在这里修改参数来可视化不同的网络
    # 星座类型可选: 'globalstar', 'iridium'
    visualize_topology_3d(constellation_type='globalstar', num_ground_stations=15)