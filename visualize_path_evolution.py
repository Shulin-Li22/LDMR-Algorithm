#!/usr/bin/env python3
"""
LDMR算法路径随时间演进的可视化工具
作者：Gemini
描述：此脚本生成一系列图像，展示从A地到B地的最优路径如何随卫星拓扑的变化而动态调整。
      这些图像可以被合成为一个动画。
"""

import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import List, Optional

# --- 添加项目路径 ---
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

try:
    # --- 导入核心类 ---
    from topology.satellite_constellation import LEONetworkBuilder, GroundStationManager
    from topology.topology_base import NodeType, NetworkTopology
    from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig
    from traffic.traffic_model import TrafficDemand
except ImportError as e:
    print(f"错误：无法导入项目模块: {e}")
    sys.exit(1)


# --- 导入我们之前编写的3D绘图函数 ---
# (为了让此脚本独立，我们直接从之前的脚本中复制这个函数)
def draw_3d_topology_with_paths(
        topology: NetworkTopology,
        title: str,
        output_filename: str,
        highlight_paths: Optional[List] = None
):
    """
    绘制带有高亮路径的3D拓扑图的辅助函数。
    """
    fig = plt.figure(figsize=(20, 18))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制地球
    earth_radius = GroundStationManager().lat_lon_to_cartesian(0, 0).x
    u, v = np.mgrid[0:2 * np.pi:100j, 0:np.pi:100j]
    x = earth_radius * np.cos(u) * np.sin(v)
    y = earth_radius * np.sin(u) * np.sin(v)
    z = earth_radius * np.cos(v)
    ax.plot_surface(x, y, z, color='lightblue', alpha=0.2, rstride=5, cstride=5)

    # 绘制节点和链路 (背景)
    nodes = topology.nodes.values()
    all_sat = [n for n in nodes if n.type == NodeType.SATELLITE]
    all_gs = [n for n in nodes if n.type == NodeType.GROUND_STATION]

    for link in topology.links.values():
        n1, n2 = topology.nodes[link.node1_id], topology.nodes[link.node2_id]
        ax.plot([n1.position.x, n2.position.x], [n1.position.y, n2.position.y], [n1.position.z, n2.position.z],
                color='#e0e0e0', linewidth=0.5, alpha=0.4)

    ax.scatter([n.position.x for n in all_sat], [n.position.y for n in all_sat], [n.position.z for n in all_sat],
               c='#d0d0d0', marker='o', s=15)
    ax.scatter([n.position.x for n in all_gs], [n.position.y for n in all_gs], [n.position.z for n in all_gs],
               c='#d0d0d0', marker='s', s=30)

    # 绘制高亮路径
    path_colors = ['#2E8B57', '#4682B4', '#D2691E']  # Green, Blue, Orange
    if highlight_paths:
        start_node_id = highlight_paths[0].nodes[0]
        end_node_id = highlight_paths[0].nodes[-1]

        for i, path in enumerate(highlight_paths):
            path_nodes_obj = [topology.nodes[node_id] for node_id in path.nodes]
            color = path_colors[i % len(path_colors)]

            for j in range(len(path_nodes_obj) - 1):
                n1, n2 = path_nodes_obj[j], path_nodes_obj[j + 1]
                ax.plot([n1.position.x, n2.position.x], [n1.position.y, n2.position.y], [n1.position.z, n2.position.z],
                        color=color, linewidth=2.5)

            path_sat = [n for n in path_nodes_obj if n.type == NodeType.SATELLITE]
            ax.scatter([n.position.x for n in path_sat], [n.position.y for n in path_sat],
                       [n.position.z for n in path_sat], c=color, marker='o', s=50, depthshade=True)

        start_node = topology.nodes[start_node_id]
        end_node = topology.nodes[end_node_id]
        ax.scatter([start_node.position.x, end_node.position.x], [start_node.position.y, end_node.position.y],
                   [start_node.position.z, end_node.position.z],
                   c='#FFD700', marker='*', s=400, edgecolor='black', label='Start/End Points', depthshade=True)

    # 美化图表
    ax.set_title(title, fontsize=24, fontweight='bold')
    ax.set_xlabel('X (km)'), ax.set_ylabel('Y (km)'), ax.set_zlabel('Z (km)')
    ax.legend(loc='upper left', bbox_to_anchor=(0.8, 0.95))

    max_range = np.array([n.position.x for n in all_sat]).max() * 1.1 if all_sat else 8000
    ax.set_xlim([-max_range, max_range]), ax.set_ylim([-max_range, max_range]), ax.set_zlim([-max_range, max_range])
    ax.view_init(elev=25., azim=60)

    # 确保输出目录存在
    output_dir = project_root / 'results' / 'figures' / 'evolution_frames'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename

    plt.savefig(output_path, dpi=150, bbox_inches='tight')  # 使用较低的DPI以加快生成速度
    plt.close(fig)
    print(f"✅ 已生成动画帧: {output_path}")


def generate_path_evolution_frames():
    """
    主函数，用于生成路径随时间演变的动画帧。
    """
    print("\n--- 🚀 开始生成路径演进动画帧 ---")

    # --- 1. 动画参数设置 ---
    SIMULATION_DURATION = 2400  # 总仿真时长 (秒)
    TIME_STEP = 60  # 时间步长 (秒) -> 每30秒生成一帧

    # --- 2. 生成时间序列拓扑 ---
    # 这是关键一步，我们一次性生成所有时间点的拓扑快照
    print(f"🔧 正在生成从 t=0 到 t={SIMULATION_DURATION}s 的时间序列拓扑...")
    builder = LEONetworkBuilder('globalstar', 15)
    # build_time_series 方法返回一个 TopologyManager 对象，其中包含所有快照
    topology_manager = builder.build_time_series(duration=SIMULATION_DURATION, time_step=TIME_STEP)

    # --- 3. 设定固定的流量需求 ---
    # 我们将在所有时间点上，为同一对GS计算路径
    initial_topology = topology_manager.get_snapshot_at_time(0).topology
    gs_nodes = [node for node in initial_topology.nodes.values() if node.type == NodeType.GROUND_STATION]
    source_node_id = next((gs.id for gs in gs_nodes if gs.attributes.get('city') == 'New_York'), gs_nodes[0].id)
    dest_node_id = next((gs.id for gs in gs_nodes if gs.attributes.get('city') == 'London'), gs_nodes[1].id)
    demand = TrafficDemand(source_node_id, dest_node_id, 100, 0, SIMULATION_DURATION)

    print(f"🔧 固定流量需求: 从 {source_node_id} 到 {dest_node_id}")

    # --- 4. 循环遍历每个时间点，计算路径并生成图像 ---
    ldmr_config = LDMRConfig(K=2)
    ldmr_algo = LDMRAlgorithm(ldmr_config)

    for i, snapshot in enumerate(topology_manager.snapshots):
        current_time = snapshot.timestamp
        current_topology = snapshot.topology
        print(f"\n--- 计算时间点 t = {current_time:.0f}s ---")

        # 在当前拓扑上运行LDMR算法
        # 注意：这里我们为简化，每次都new一个LDMR对象，以重置其内部状态
        # 在真实的连续仿真中，状态可能会被保留
        results = ldmr_algo.run_ldmr_algorithm(current_topology, [demand])

        # 提取路径用于高亮
        calculated_paths = results[0].paths if results and results[0].success else []

        # 生成并保存当前帧的3D图像
        draw_3d_topology_with_paths(
            topology=current_topology,
            title=f"Path Evolution at T = {current_time:.0f} seconds",
            output_filename=f"frame_{i:03d}.png",  # 格式化命名，如 frame_000.png, frame_001.png
            highlight_paths=calculated_paths
        )

    print("\n--- ✅ 所有动画帧生成完毕！---")


if __name__ == '__main__':
    generate_path_evolution_frames()