#!/usr/bin/env python3
"""
LDMR算法执行流程的3D可视化工具 (已修复NameError)
作者：Gemini
描述：此脚本用于在3D空间中可视化LDMR算法的核心步骤，并用明确的标记和打印输出来解决节点重叠的视觉混淆问题。
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import List, Optional, Set, Tuple, Dict

# --- 添加项目路径 ---
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

try:
    # --- 导入核心类 ---
    from topology.satellite_constellation import LEONetworkBuilder, GroundStationManager
    from topology.topology_base import NodeType, NetworkTopology
    from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig
    from algorithms.basic_algorithms import DijkstraPathFinder, PathInfo
    from traffic.traffic_model import TrafficDemand
except ImportError as e:
    print(f"错误：无法导入项目模块: {e}")
    sys.exit(1)


def draw_3d_topology_with_paths(
        topology: NetworkTopology,
        title: str,
        output_filename: str,
        highlight_paths: Optional[List[PathInfo]] = None
):
    """
    绘制带有高亮路径的3D拓扑图的辅助函数。
    """
    fig = plt.figure(figsize=(20, 18))
    ax = fig.add_subplot(111, projection='3d')

    # --- 1. 绘制地球 ---
    earth_radius = GroundStationManager().lat_lon_to_cartesian(0, 0).x
    u, v = np.mgrid[0:2 * np.pi:100j, 0:np.pi:100j]
    x = earth_radius * np.cos(u) * np.sin(v)
    y = earth_radius * np.sin(u) * np.sin(v)
    z = earth_radius * np.cos(v)
    ax.plot_surface(x, y, z, color='lightblue', alpha=0.2, rstride=5, cstride=5)

    # --- 2. 绘制所有节点和链路 (背景) ---
    nodes = topology.nodes.values()
    all_sat = [n for n in nodes if n.type == NodeType.SATELLITE]
    all_gs = [n for n in nodes if n.type == NodeType.GROUND_STATION]

    for link in topology.links.values():
        n1, n2 = topology.nodes[link.node1_id], topology.nodes[link.node2_id]
        ax.plot([n1.position.x, n2.position.x], [n1.position.y, n2.position.y], [n1.position.z, n2.position.z],
                color='#e0e0e0', linewidth=0.5, alpha=0.4)

    ax.scatter([n.position.x for n in all_sat], [n.position.y for n in all_sat], [n.position.z for n in all_sat],
               c='#d0d0d0', marker='o', s=15, label='Satellite (Inactive)')
    ax.scatter([n.position.x for n in all_gs], [n.position.y for n in all_gs], [n.position.z for n in all_gs],
               c='#d0d0d0', marker='s', s=30, label='Ground Station (Inactive)')

    # --- 3. 绘制高亮路径 ---
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

    # --- 4. 美化图表 ---
    ax.set_title(title, fontsize=24, fontweight='bold')
    ax.set_xlabel('X (km)'), ax.set_ylabel('Y (km)'), ax.set_zlabel('Z (km)')
    ax.legend(loc='upper left', bbox_to_anchor=(0.8, 0.95))

    max_range = np.array([n.position.x for n in all_sat]).max() * 1.1 if all_sat else 8000
    ax.set_xlim([-max_range, max_range]), ax.set_ylim([-max_range, max_range]), ax.set_zlim([-max_range, max_range])
    ax.view_init(elev=25., azim=60)

    output_dir = project_root / 'results' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 3D可视化图表已保存至: {output_path}")


def visualize_single_demand_flow_3d():
    print("\n--- 🚀 开始3D可视化：单需求多路径计算流程 (已修复) ---")

    builder = LEONetworkBuilder('globalstar', 15)
    topology = builder.build_network()

    gs_nodes = [node for node in topology.nodes.values() if node.type == NodeType.GROUND_STATION]

    # *** BUG修复开始 ***
    # 修正了NameError，将 'in' 改为 'if'
    source_node_id = next((gs.id for gs in gs_nodes if gs.attributes.get('city') == 'New_York'), gs_nodes[0].id)
    dest_node_id = next((gs.id for gs in gs_nodes if gs.attributes.get('city') == 'London'), gs_nodes[1].id)
    # *** BUG修复结束 ***

    demand = TrafficDemand(source_node_id, dest_node_id, 100, 0, 10)

    print(f"🔧 流量需求: 从 {source_node_id} 到 {dest_node_id}")

    config = LDMRConfig(K=2)
    ldmr_algo = LDMRAlgorithm(config)

    path_finder = DijkstraPathFinder(topology)
    path1 = path_finder.find_shortest_path(demand.source_id, demand.destination_id, weight_type='delay')

    if not path1:
        print("❌ 无法找到初始路径，可视化失败。")
        return

    excluded_links = {tuple(sorted(link)) for link in path1.links}
    path2 = ldmr_algo.find_backup_path_with_excluded_links(
        topology, demand.source_id, demand.destination_id, excluded_links
    )

    print("\n" + "=" * 50)
    print("算法计算出的路径节点ID序列:")
    print(f"Path 1 (绿色): {' -> '.join(path1.nodes)}")
    if path2:
        print(f"Path 2 (蓝色): {' -> '.join(path2.nodes)}")
    else:
        print("Path 2 (蓝色): 未找到")
    print("=" * 50 + "\n")

    final_paths = [path1]
    if path2:
        final_paths.append(path2)

    draw_3d_topology_with_paths(
        topology,
        title="3D View: Final Link-Disjoint Multipath",
        output_filename="flow_3d_final_verified.png",
        highlight_paths=final_paths
    )

    print("--- ✅ 单需求多路径计算流程3D可视化完成 ---\n")


if __name__ == '__main__':
    visualize_single_demand_flow_3d()