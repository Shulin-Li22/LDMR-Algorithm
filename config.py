#!/usr/bin/env python3
"""
简化配置管理
直接读取yaml文件，无复杂逻辑
"""

import yaml
import os
from pathlib import Path


def load_config(config_file='config/default.yaml'):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_file}")
        return get_default_config()
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return get_default_config()


def get_default_config():
    """默认配置"""
    return {
        'network': {
            'constellation': 'globalstar',
            'ground_stations': 10,
            'satellite_bandwidth': 10.0,
            'ground_bandwidth': 5.0
        },
        'algorithm': {
            'K': 2,
            'r1': 1,
            'r2': 10,
            'r3': 50,
            'Ne_th': 2,
            'enable_statistics': True
        },
        'traffic': {
            'total_gbps': 6.0,
            'duration': 180.0,
            'elephant_ratio': 0.3
        }
    }


def list_scenarios():
    """列出可用场景"""
    scenarios_dir = Path('config/scenarios')
    if not scenarios_dir.exists():
        return []

    scenarios = []
    for file in scenarios_dir.glob('*.yaml'):
        scenarios.append(file.stem)
    return scenarios


def load_scenario(scenario_name):
    """加载场景配置"""
    scenario_file = f'config/scenarios/{scenario_name}.yaml'
    scenario_config = load_config(scenario_file)

    # 与默认配置合并
    default_config = get_default_config()
    merge_config(default_config, scenario_config)

    return default_config


def merge_config(base, override):
    """合并配置"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            merge_config(base[key], value)
        else:
            base[key] = value


def save_current_scenario(scenario_name):
    """保存当前场景（简化版本）"""
    current_file = 'config/current_scenario.txt'
    with open(current_file, 'w') as f:
        f.write(scenario_name)


def get_current_scenario():
    """获取当前场景"""
    current_file = 'config/current_scenario.txt'
    if os.path.exists(current_file):
        with open(current_file, 'r') as f:
            return f.read().strip()
    return 'default'