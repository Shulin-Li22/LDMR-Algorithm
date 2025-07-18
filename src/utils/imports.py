"""
项目导入工具
统一处理项目内模块导入
"""

import sys
import os
from pathlib import Path


def setup_project_path():
    """设置项目路径"""
    # 获取项目根目录
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # 向上两级到项目根目录
    src_dir = project_root / 'src'
    
    # 添加到Python路径
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    return project_root, src_dir


def safe_import(module_name, package=None):
    """安全导入模块"""
    try:
        if package:
            return __import__(f"{package}.{module_name}", fromlist=[module_name])
        else:
            return __import__(module_name)
    except ImportError as e:
        print(f"警告：无法导入模块 {module_name}: {e}")
        return None


# 自动设置路径
PROJECT_ROOT, SRC_DIR = setup_project_path()


# 常用导入别名
def import_topology():
    """导入拓扑相关模块"""
    from topology.topology_base import NetworkTopology, Node, Link, Position, NodeType
    from topology.satellite_constellation import LEONetworkBuilder, SatelliteConstellation
    return NetworkTopology, Node, Link, Position, NodeType, LEONetworkBuilder, SatelliteConstellation


def import_algorithms():
    """导入算法相关模块"""
    from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig, MultiPathResult
    from algorithms.basic_algorithms import DijkstraPathFinder, PathInfo
    return LDMRAlgorithm, LDMRConfig, MultiPathResult, DijkstraPathFinder, PathInfo


def import_traffic():
    """导入流量相关模块"""
    from traffic.traffic_model import TrafficGenerator, TrafficDemand
    return TrafficGenerator, TrafficDemand


def import_config():
    """导入配置相关模块"""
    from config import load_default_config, load_scenario_config
    from config.validator import validate_config
    return load_default_config, load_scenario_config, validate_config


def import_runner():
    """导入运行器相关模块"""
    from runner import LDMRRunner, setup_logger
    return LDMRRunner, setup_logger


def import_baseline():
    """导入基准算法模块"""
    from algorithms.baseline import SPFAlgorithm, ECMPAlgorithm, BenchmarkManager
    return SPFAlgorithm, ECMPAlgorithm, BenchmarkManager


# 全局导入检查
def check_dependencies():
    """检查项目依赖"""
    required_packages = [
        'numpy', 'scipy', 'pandas', 'networkx', 
        'matplotlib', 'seaborn', 'yaml', 'plotly'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True
