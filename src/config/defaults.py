"""
默认值定义
定义各种配置的默认值
"""

# 仿真默认值
SIMULATION_DEFAULTS = {
    'name': 'LDMR Simulation',
    'version': '1.0',
    'description': 'LDMR算法仿真'
}

# 网络默认值
NETWORK_DEFAULTS = {
    'constellation': 'globalstar',
    'ground_stations': 10,
    'satellite_bandwidth': 10.0,
    'ground_bandwidth': 5.0
}

# 算法默认值
ALGORITHM_DEFAULTS = {
    'name': 'LDMR',
    'config': {
        'K': 2,
        'r1': 1,
        'r2': 10,
        'r3': 50,
        'Ne_th': 2,
        'max_iterations': 10,
        'enable_statistics': True
    }
}

# 流量默认值
TRAFFIC_DEFAULTS = {
    'total_gbps': 6.0,
    'duration': 180.0,
    'elephant_ratio': 0.3,
    'elephant_threshold': 50.0
}

# 流量生成默认值
TRAFFIC_GENERATION_DEFAULTS = {
    'alpha': 0.5,
    'beta': 2.0,
    'pareto_shape_on': 1.5,
    'pareto_scale_on': 500,
    'pareto_shape_off': 1.5,
    'pareto_scale_off': 1000
}

# 输出默认值
OUTPUT_DEFAULTS = {
    'results_dir': 'results',
    'log_dir': 'logs',
    'auto_timestamp': True,
    'save_detailed_paths': False,
    'save_logs': True,
    'log_level': 'INFO',
    'console_output': True
}

# 监控默认值
MONITORING_DEFAULTS = {
    'enable_real_time_stats': True,
    'progress_update_interval': 1000,
    'memory_monitoring': False
}

# 验证默认值
VALIDATION_DEFAULTS = {
    'verify_path_disjointness': True,
    'check_network_connectivity': True,
    'validate_traffic_demands': True
}

# 合并所有默认值
DEFAULT_VALUES = {
    'simulation': SIMULATION_DEFAULTS,
    'network': NETWORK_DEFAULTS,
    'algorithm': ALGORITHM_DEFAULTS,
    'traffic': TRAFFIC_DEFAULTS,
    'traffic_generation': TRAFFIC_GENERATION_DEFAULTS,
    'output': OUTPUT_DEFAULTS,
    'monitoring': MONITORING_DEFAULTS,
    'validation': VALIDATION_DEFAULTS
}

# 支持的星座类型
SUPPORTED_CONSTELLATIONS = ['globalstar', 'iridium']

# 支持的算法
SUPPORTED_ALGORITHMS = ['LDMR', 'SPF', 'ECMP']

# 支持的日志级别
SUPPORTED_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

# 参数范围限制
PARAMETER_LIMITS = {
    'network': {
        'ground_stations': {'min': 1, 'max': 50},
        'satellite_bandwidth': {'min': 0.1, 'max': 100.0},
        'ground_bandwidth': {'min': 0.1, 'max': 100.0}
    },
    'algorithm': {
        'K': {'min': 1, 'max': 10},
        'r1': {'min': 1, 'max': 100},
        'r2': {'min': 1, 'max': 100},
        'r3': {'min': 1, 'max': 200},
        'Ne_th': {'min': 1, 'max': 20},
        'max_iterations': {'min': 1, 'max': 100}
    },
    'traffic': {
        'total_gbps': {'min': 0.1, 'max': 50.0},
        'duration': {'min': 10.0, 'max': 3600.0},
        'elephant_ratio': {'min': 0.0, 'max': 1.0},
        'elephant_threshold': {'min': 1.0, 'max': 1000.0}
    }
}
