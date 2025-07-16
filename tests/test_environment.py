#!/usr/bin/env python3
"""
LDMR算法环境测试脚本
验证所有组件是否正常工作
"""

import sys
import os
import traceback
from typing import Dict, Any

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print(f"项目根目录: {project_root}")
print(f"源代码目录: {src_dir}")


def test_package_imports() -> Dict[str, bool]:
    """测试包导入"""
    test_results = {}

    packages = [
        ('numpy', 'import numpy as np'),
        ('pandas', 'import pandas as pd'),
        ('matplotlib', 'import matplotlib.pyplot as plt'),
        ('networkx', 'import networkx as nx'),
        ('scipy', 'import scipy'),
        ('sklearn', 'import sklearn'),
        ('seaborn', 'import seaborn as sns'),
        ('plotly', 'import plotly.graph_objects as go'),
    ]

    print("\n测试基础包导入...")
    for package_name, import_statement in packages:
        try:
            exec(import_statement)
            test_results[package_name] = True
            print(f"✅ {package_name} - 导入成功")
        except ImportError as e:
            test_results[package_name] = False
            print(f"❌ {package_name} - 导入失败: {e}")
        except Exception as e:
            test_results[package_name] = False
            print(f"❌ {package_name} - 其他错误: {e}")

    return test_results


def test_topology_components():
    """测试拓扑组件"""
    print("\n测试拓扑组件...")

    try:
        from topology.topology_base import (
            NetworkTopology, Node, Link, Position, NodeType,
            TopologySnapshot, TopologyManager
        )
        print("✅ topology_base - 导入成功")

        # 测试基础功能
        topology = NetworkTopology()
        node1 = Node("test1", NodeType.SATELLITE, Position(0, 0, 0))
        node2 = Node("test2", NodeType.GROUND_STATION, Position(1, 1, 1))

        topology.add_node(node1)
        topology.add_node(node2)

        link = Link("test1", "test2", 10.0, 5.0)
        topology.add_link(link)

        stats = topology.get_statistics()
        assert stats['total_nodes'] == 2
        assert stats['total_links'] == 1

        print("✅ 基础拓扑功能 - 测试通过")
        return True

    except Exception as e:
        print(f"❌ 拓扑组件测试失败: {e}")
        traceback.print_exc()
        return False


def test_constellation_builder():
    """测试星座构建器"""
    print("\n测试星座构建器...")

    try:
        from topology.satellite_constellation import (
            SatelliteConstellation, GroundStationManager, LEONetworkBuilder
        )
        print("✅ satellite_constellation - 导入成功")

        # 测试GlobalStar星座
        constellation = SatelliteConstellation('globalstar')
        satellites = constellation.generate_satellite_nodes(time=0)

        assert len(satellites) == 48
        print("✅ GlobalStar星座生成 - 测试通过")

        # 测试地面站
        gs_manager = GroundStationManager()
        ground_stations = gs_manager.generate_ground_stations(5)

        assert len(ground_stations) == 5
        print("✅ 地面站生成 - 测试通过")

        # 测试完整网络构建
        builder = LEONetworkBuilder('globalstar', 5)
        network = builder.build_network()

        stats = network.get_statistics()
        assert stats['satellites'] == 48
        assert stats['ground_stations'] == 5

        print("✅ 完整网络构建 - 测试通过")
        return True

    except Exception as e:
        print(f"❌ 星座构建器测试失败: {e}")
        traceback.print_exc()
        return False


def test_traffic_generator():
    """测试流量生成器"""
    print("\n测试流量生成器...")

    try:
        from traffic.traffic_model import (
            TrafficGenerator, TrafficDemand, ParetoFlowGenerator,
            PopulationZone, TrafficMatrix
        )
        print("✅ traffic_model - 导入成功")

        # 测试流量矩阵
        traffic_matrix = TrafficMatrix()
        zones = traffic_matrix.generate_default_zones(5)
        matrix = traffic_matrix.calculate_traffic_matrix(total_traffic=10.0)

        assert len(zones) == 5
        assert len(matrix) > 0
        print("✅ 流量矩阵生成 - 测试通过")

        # 测试Pareto流量生成
        pareto_gen = ParetoFlowGenerator()
        flows = pareto_gen.generate_flow_sequence(duration=100.0, avg_bandwidth=50.0)

        assert len(flows) > 0
        print("✅ Pareto流量生成 - 测试通过")

        # 测试综合流量生成
        generator = TrafficGenerator()
        gs_list = [f"GS_{i}" for i in range(5)]
        demands = generator.generate_traffic_demands(gs_list, total_traffic=5.0, duration=100.0)

        assert len(demands) > 0
        stats = generator.get_flow_statistics(demands)
        assert 'total_flows' in stats

        print("✅ 综合流量生成 - 测试通过")
        return True

    except Exception as e:
        print(f"❌ 流量生成器测试失败: {e}")
        traceback.print_exc()
        return False


def test_basic_algorithms():
    """测试基础算法"""
    print("\n测试基础算法...")

    try:
        from algorithms.basic_algorithms import (
            DijkstraPathFinder, LinkDisjointPathFinder, PathInfo,
            GraphOperations, PathQualityEvaluator, NetworkConnectivityAnalyzer
        )
        print("✅ basic_algorithms - 导入成功")

        # 创建简单测试拓扑
        from topology.topology_base import NetworkTopology, Node, Link, Position, NodeType

        topology = NetworkTopology()

        # 添加节点
        nodes = [
            Node("A", NodeType.SATELLITE, Position(0, 0, 0)),
            Node("B", NodeType.SATELLITE, Position(1, 0, 0)),
            Node("C", NodeType.GROUND_STATION, Position(2, 0, 0))
        ]

        for node in nodes:
            topology.add_node(node)

        # 添加链路
        links = [
            Link("A", "B", 10.0, 10.0),
            Link("B", "C", 10.0, 15.0),
            Link("A", "C", 10.0, 20.0)
        ]

        for link in links:
            topology.add_link(link)

        # 测试Dijkstra算法
        finder = DijkstraPathFinder(topology)
        path = finder.find_shortest_path("A", "C")

        assert path is not None
        assert path.nodes[0] == "A"
        assert path.nodes[-1] == "C"

        print("✅ Dijkstra算法 - 测试通过")

        # 测试链路不相交路径
        disjoint_finder = LinkDisjointPathFinder(topology)
        paths = disjoint_finder.find_link_disjoint_paths("A", "C", k=2)

        assert len(paths) <= 2
        print("✅ 链路不相交路径 - 测试通过")

        # 测试路径质量评估
        evaluator = PathQualityEvaluator(topology)
        quality = evaluator.evaluate_path_quality(path)

        assert 0 <= quality <= 1
        print("✅ 路径质量评估 - 测试通过")

        return True

    except Exception as e:
        print(f"❌ 基础算法测试失败: {e}")
        traceback.print_exc()
        return False


def test_integration():
    """测试组件集成"""
    print("\n测试组件集成...")

    try:
        # 导入所有组件
        from topology.satellite_constellation import LEONetworkBuilder
        from traffic.traffic_model import TrafficGenerator
        from algorithms.basic_algorithms import DijkstraPathFinder

        # 构建完整系统
        print("  构建LEO网络...")
        builder = LEONetworkBuilder('globalstar', 10)
        topology = builder.build_network()

        print("  生成流量需求...")
        generator = TrafficGenerator()
        gs_list = [node.id for node in topology.nodes.values()
                   if node.type.value == 'ground_station']
        demands = generator.generate_traffic_demands(gs_list[:5], total_traffic=2.0, duration=60.0)

        print("  计算路径...")
        path_finder = DijkstraPathFinder(topology)

        test_demand = demands[0] if demands else None
        if test_demand:
            path = path_finder.find_shortest_path(test_demand.source_id, test_demand.destination_id)
            if path:
                print(f"    找到路径: {path.nodes[0]} -> {path.nodes[-1]} ({len(path.nodes)}跳)")
            else:
                print("    未找到路径")

        print("✅ 组件集成 - 测试通过")
        return True

    except Exception as e:
        print(f"❌ 组件集成测试失败: {e}")
        traceback.print_exc()
        return False


def generate_test_report(results: Dict[str, bool]) -> str:
    """生成测试报告"""
    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests

    report = f"""
================== LDMR 环境测试报告 ==================

总测试数: {total_tests}
通过数: {passed_tests} 
失败数: {failed_tests}
成功率: {passed_tests / total_tests * 100:.1f}%

详细结果:
"""

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        report += f"  {test_name:<25} {status}\n"

    if failed_tests == 0:
        report += "\n🎉 所有测试通过！环境配置成功！"
    else:
        report += f"\n⚠️  有 {failed_tests} 项测试失败，请检查环境配置"

    report += "\n" + "=" * 55

    return report


def main():
    """主测试函数"""
    print("🚀 开始LDMR算法环境测试...")

    test_results = {}

    # 运行各项测试
    try:
        # 基础包测试
        package_results = test_package_imports()
        test_results.update(package_results)

        # 组件测试
        test_results['topology_components'] = test_topology_components()
        test_results['constellation_builder'] = test_constellation_builder()
        test_results['traffic_generator'] = test_traffic_generator()
        test_results['basic_algorithms'] = test_basic_algorithms()
        test_results['integration'] = test_integration()

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return
    except Exception as e:
        print(f"\n❌ 测试过程中发生未预期错误: {e}")
        traceback.print_exc()
        return

    # 生成并显示报告
    report = generate_test_report(test_results)
    print(report)

    # 返回退出码
    all_passed = all(test_results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()