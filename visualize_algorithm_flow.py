#!/usr/bin/env python3
"""
LDMR算法执行流程可视化工具
作者：Gemini
描述：此脚本用于可视化LDMR算法的核心步骤，包括单流量需求的多路径计算过程和网络负载均衡情况。
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from typing import List, Optional, Set, Tuple, Dict

# --- 关键步骤 1: 添加项目路径，确保可以正确导入模块 ---
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))
# 为了在脚本中直接运行，需要将根目录也加入，以便导入config
sys.path.insert(0, str(project_root))

try:
    # --- 关键步骤 2: 导入项目中的核心类 ---
    from topology.satellite_constellation import LEONetworkBuilder
    from topology.topology_base import NodeType, NetworkTopology, Position
    from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig
    from algorithms.basic_algorithms import DijkstraPathFinder, PathInfo
    from traffic.traffic_model import TrafficGenerator, TrafficDemand
    from config import load_config
except ImportError as e:
    print("错误：无法导入项目模块。")
    print(f"请确保此脚本位于 'ldmr-algorithm' 项目的根目录下，并且 'src' 目录存在。")
    print(f"详细错误: {e}")
    sys.exit(1)


def draw_topology_with_paths(
        topology: NetworkTopology,
        pos: Dict[str, Tuple[float, float]],
        title: str,
        output_filename: str,
        highlight_paths: Optional[List[PathInfo]] = None,
        excluded_links: Optional[Set[Tuple[str, str]]] = None,
        link_styles: Optional[Dict[Tuple[str, str], Dict]] = None
):
    """
    绘制带有高亮路径和自定义样式的拓扑图的辅助函数。

    Args:
        topology (NetworkTopology): 网络拓扑.
        pos (Dict): 节点位置.
        title (str): 图表标题.
        output_filename (str): 输出文件名.
        highlight_paths (Optional[List[PathInfo]]): 需要高亮的路径列表.
        excluded_links (Optional[Set[Tuple[str, str]]]): 需要特殊标记的排除链路.
        link_styles (Optional[Dict[Tuple[str, str], Dict]]): 链路的自定义样式 (颜色, 粗细).
    """
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(20, 16))

    graph = topology.graph
    satellite_nodes = [node.id for node in topology.nodes.values() if node.type == NodeType.SATELLITE]
    ground_station_nodes = [node.id for node in topology.nodes.values() if node.type == NodeType.GROUND_STATION]

    # --- 绘制基础网络 ---
    # 绘制所有链路 (默认样式: 灰色，细线)
    nx.draw_networkx_edges(graph, pos, ax=ax, edge_color='#cccccc', width=0.7, alpha=0.8)

    # 绘制所有节点 (基础颜色)
    nx.draw_networkx_nodes(graph, pos, ax=ax, nodelist=satellite_nodes, node_color='#B0C4DE', node_size=80,
                           node_shape='o')
    nx.draw_networkx_nodes(graph, pos, ax=ax, nodelist=ground_station_nodes, node_color='#ADD8E6', node_size=150,
                           node_shape='s')

    # --- 绘制自定义和高亮部分 ---
    if link_styles:
        for link, styles in link_styles.items():
            nx.draw_networkx_edges(graph, pos, ax=ax, edgelist=[link], **styles)

    if excluded_links:
        nx.draw_networkx_edges(
            graph, pos, ax=ax,
            edgelist=list(excluded_links),
            edge_color='red',
            width=2.0,
            style='dotted',
            alpha=0.8
        )

    path_colors = ['#2E8B57', '#4682B4', '#D2691E']  # 绿色, 蓝色, 橙色
    if highlight_paths:
        for i, path in enumerate(highlight_paths):
            path_edges = list(zip(path.nodes, path.nodes[1:]))
            color = path_colors[i % len(path_colors)]
            nx.draw_networkx_edges(
                graph, pos, ax=ax,
                edgelist=path_edges,
                edge_color=color,
                width=2.5,
                alpha=1.0
            )
            # *** BUG修复开始 ***
            # 高亮路径上的节点时，要区分卫星和地面站的形状
            path_gs_nodes = [node_id for node_id in path.nodes if node_id in ground_station_nodes]
            path_sat_nodes = [node_id for node_id in path.nodes if node_id in satellite_nodes]

            # 绘制高亮的卫星 (圆形)
            nx.draw_networkx_nodes(graph, pos, ax=ax, nodelist=path_sat_nodes, node_color=color, node_size=120,
                                   node_shape='o')
            # 绘制高亮的地面站 (方形)
            nx.draw_networkx_nodes(graph, pos, ax=ax, nodelist=path_gs_nodes, node_color=color, node_size=180,
                                   node_shape='s')
            # *** BUG修复结束 ***

    # --- 美化图表 ---
    ax.set_title(title, fontsize=24, fontweight='bold')
    ax.set_xlabel("X-axis Projection", fontsize=12)
    ax.set_ylabel("Y-axis Projection", fontsize=12)
    fig.tight_layout()

    # 创建输出目录并保存图像
    output_dir = project_root / 'results' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)  # 关闭图像，释放内存
    print(f"✅ 可视化图表已保存至: {output_path}")


def visualize_single_demand_flow():
    """
    可视化LDMR算法为单个流量需求计算多路径的核心流程。
    """
    print("\n--- 🚀 开始可视化：单需求多路径计算流程 ---")

    # --- 1. 环境设置 ---
    constellation_type = 'globalstar'
    num_ground_stations = 15
    builder = LEONetworkBuilder(constellation_type, num_ground_stations)
    topology = builder.build_network()

    # 选择一个有代表性的流量需求（例如，纽约到伦敦）
    gs_nodes = [node for node in topology.nodes.values() if node.type == NodeType.GROUND_STATION]
    source_node_id = next((gs.id for gs in gs_nodes if gs.attributes.get('city') == 'New_York'), gs_nodes[0].id)
    dest_node_id = next((gs.id for gs in gs_nodes if gs.attributes.get('city') == 'London'), gs_nodes[1].id)
    demand = TrafficDemand(source_node_id, dest_node_id, 100, 0, 10)

    print(f"🔧 流量需求: 从 {source_node_id} 到 {dest_node_id}")

    pos = {node.id: (node.position.x, node.position.y) for node in topology.nodes.values()}
    config = LDMRConfig(K=2)
    ldmr_algo = LDMRAlgorithm(config)

    # --- 2. 步骤一: 计算第一条最短延迟路径 ---
    print("🎨 步骤 1: 计算第一条最短延迟路径 (Path 1)...")
    path_finder = DijkstraPathFinder(topology)
    path1 = path_finder.find_shortest_path(demand.source_id, demand.destination_id, weight_type='delay')
    if not path1:
        print("❌ 无法找到初始路径，可视化失败。")
        return

    draw_topology_with_paths(
        topology, pos,
        title="Step 1: Find Shortest Path by Delay (Path 1)",
        output_filename="flow_step1_shortest_path.png",
        highlight_paths=[path1]
    )

    # --- 3. 步骤二: 寻找第二条链路不相交的路径 ---
    print("🎨 步骤 2: 排除已用链路，更新权重，寻找备用路径 (Path 2)...")
    excluded_links_for_path2 = {tuple(sorted(link)) for link in path1.links}

    path2 = ldmr_algo.find_backup_path_with_excluded_links(
        topology, demand.source_id, demand.destination_id, excluded_links_for_path2
    )
    if not path2:
        print("⚠️ 未能找到第二条不相交路径。")

    draw_topology_with_paths(
        topology, pos,
        title="Step 2: Find Backup Path (Path 2) by Excluding Path 1's Links",
        output_filename="flow_step2_backup_path.png",
        highlight_paths=[path1, path2] if path2 else [path1],
        excluded_links=excluded_links_for_path2
    )

    # --- 4. 步骤三: 最终结果 ---
    print("🎨 步骤 3: 展示最终计算出的两条链路不相交路径...")
    final_paths = [path1]
    if path2:
        final_paths.append(path2)

    draw_topology_with_paths(
        topology, pos,
        title="Step 3: Final Link-Disjoint Multipath Result",
        output_filename="flow_step3_final_result.png",
        highlight_paths=final_paths
    )
    print("--- ✅ 单需求多路径计算流程可视化完成 ---\n")


def visualize_load_balancing():
    """
    可视化一轮完整仿真后的网络链路使用情况，以展示负载均衡效果。
    """
    print("--- 🚀 开始可视化：网络负载均衡热力图 ---")

    # --- 1. 运行一轮完整的LDMR仿真来收集数据 ---
    config = load_config()
    builder = LEONetworkBuilder(
        config['network']['constellation'],
        config['network']['ground_stations']
    )
    topology = builder.build_network()

    generator = TrafficGenerator()
    ground_stations = [
        node.id for node in topology.nodes.values()
        if node.type.value == 'ground_station'
    ]
    demands = generator.generate_traffic_demands(
        ground_station_ids=ground_stations,
        total_traffic=config['traffic']['total_gbps'],
        duration=config['traffic']['duration']
    )

    print(f"🔧 正在运行LDMR算法处理 {len(demands)} 个流量需求...")
    ldmr_config = LDMRConfig(K=config['algorithm']['K'], r3=config['algorithm']['r3'],
                             Ne_th=config['algorithm']['Ne_th'])
    ldmr = LDMRAlgorithm(ldmr_config)
    ldmr.run_ldmr_algorithm(topology, demands)

    link_usage = ldmr.link_usage_count
    if not link_usage:
        print("❌ 仿真未产生链路使用数据，无法生成热力图。")
        return

    # --- 2. 准备绘图数据 ---
    pos = {node.id: (node.position.x, node.position.y) for node in topology.nodes.values()}

    link_styles = {}
    max_usage = max(link_usage.values()) if link_usage else 1

    cmap = plt.get_cmap('viridis')

    for link_id, usage in link_usage.items():
        node1, node2 = link_id
        normalized_usage = usage / max_usage
        color = cmap(normalized_usage)
        width = 0.8 + normalized_usage * 2.5

        link_styles[(node1, node2)] = {
            'edge_color': color,
            'width': width,
            'alpha': 0.7 + normalized_usage * 0.3
        }

    # --- 3. 绘图 ---
    print("🎨 正在生成链路使用频次热力图...")
    draw_topology_with_paths(
        topology, pos,
        title="Network Link Usage Heatmap (Load Balancing)",
        output_filename="flow_load_balancing_heatmap.png",
        link_styles=link_styles
    )
    print("--- ✅ 网络负载均衡热力图可视化完成 ---")


if __name__ == '__main__':
    visualize_single_demand_flow()

    visualize_load_balancing()