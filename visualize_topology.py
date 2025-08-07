#!/usr/bin/env python3
"""
网络拓扑可视化工具
作者：Gemini
描述：此脚本用于生成并可视化LEO卫星网络的初始拓扑图。
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx

# --- 关键步骤 1: 添加项目路径，确保可以正确导入模块 ---
# 将项目根目录添加到Python的模块搜索路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

try:
    # --- 关键步骤 2: 导入项目中的核心类 ---
    from topology.satellite_constellation import LEONetworkBuilder
    from topology.topology_base import NodeType
except ImportError as e:
    print("错误：无法导入项目模块。")
    print(f"请确保此脚本位于 'ldmr-algorithm' 项目的根目录下，并且 'src' 目录存在。")
    print(f"详细错误: {e}")
    sys.exit(1)


def visualize_topology(constellation_type: str = 'globalstar', num_ground_stations: int = 15):
    """
    生成并可视化一个LEO卫星网络的拓扑图。

    Args:
        constellation_type (str): 星座类型, 'globalstar' 或 'iridium'。
        num_ground_stations (int): 地面站的数量。
    """
    print(f"🚀 开始生成 '{constellation_type}' 星座拓扑...")

    # --- 关键步骤 3: 使用LEONetworkBuilder构建网络 ---
    builder = LEONetworkBuilder(constellation_type, num_ground_stations)
    topology = builder.build_network(time=100)  #

    stats = topology.get_statistics()
    print(f"✅ 拓扑生成完毕: {stats['total_nodes']} 个节点, {stats['total_links']} 条链路。")
    print("🎨 开始进行可视化...")

    # --- 关键步骤 4: 提取绘图所需的数据 ---
    graph = topology.graph

    # 提取节点位置 (使用X, Y坐标进行2D投影)
    # 真实环境是3D的，这里为了简化显示，投射到2D平面
    pos = {node.id: (node.position.x, node.position.y) for node in topology.nodes.values()}

    # 将节点按类型（卫星/地面站）分类
    satellite_nodes = [node.id for node in topology.nodes.values() if node.type == NodeType.SATELLITE]
    ground_station_nodes = [node.id for node in topology.nodes.values() if node.type == NodeType.GROUND_STATION]

    # --- 关键步骤 5: 使用Matplotlib和NetworkX进行绘图 ---
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(18, 14))

    # 绘制链路 (Edges)
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edge_color='#a0a0a0',
        alpha=0.6,
        width=0.8
    )

    # 绘制卫星节点 (Satellite Nodes)
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        nodelist=satellite_nodes,
        node_color='#2E86AB',  # 蓝色
        node_size=100,
        label='Satellite'
    )

    # 绘制地面站节点 (Ground Station Nodes)
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        nodelist=ground_station_nodes,
        node_color='#A23B72',  # 紫红色
        node_size=200,
        node_shape='s',  # 方形
        label='Ground Station'
    )

    # # 如果需要，可以绘制节点标签（节点多时会显得混乱）
    # nx.draw_networkx_labels(
    #     graph,
    #     pos,
    #     ax=ax,
    #     font_size=6,
    #     font_color='black'
    # )

    # --- 关键步骤 6: 美化图表并显示 ---
    ax.set_title(f'{constellation_type.capitalize()} Constellation Network Topology', fontsize=20, fontweight='bold')
    ax.set_xlabel("X-axis Projection", fontsize=12)
    ax.set_ylabel("Y-axis Projection", fontsize=12)

    # 创建图例
    legend = ax.legend(loc='upper right', fontsize=12, frameon=True, shadow=True)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('black')

    # 移除坐标轴刻度，使图像更简洁
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    fig.tight_layout()

    # 保存图像
    output_dir = project_root / 'results' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'{constellation_type}_topology.png'
    plt.savefig(output_path, dpi=300)

    print(f"✅ 可视化图表已保存至: {output_path}")

    plt.show()


if __name__ == '__main__':
    # 您可以在这里修改参数来可视化不同的网络
    # 星座类型可选: 'globalstar', 'iridium'
    visualize_topology(constellation_type='globalstar', num_ground_stations=15)