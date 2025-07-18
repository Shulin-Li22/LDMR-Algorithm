"""
配置验证器
验证配置参数的有效性
"""

from typing import Dict, Any, List, Tuple
import os


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """验证完整配置"""
        self.errors = []
        self.warnings = []
        
        # 验证各个部分
        self._validate_simulation_config(config.get('simulation', {}))
        self._validate_network_config(config.get('network', {}))
        self._validate_algorithm_config(config.get('algorithm', {}))
        self._validate_traffic_config(config.get('traffic', {}))
        self._validate_output_config(config.get('output', {}))
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors.copy(), self.warnings.copy()
    
    def _validate_simulation_config(self, config: Dict[str, Any]):
        """验证仿真配置"""
        required_fields = ['name', 'version']
        for field in required_fields:
            if field not in config:
                self.errors.append(f"仿真配置缺少必需字段: {field}")
    
    def _validate_network_config(self, config: Dict[str, Any]):
        """验证网络配置"""
        # 验证星座类型
        constellation = config.get('constellation', '')
        valid_constellations = ['globalstar', 'iridium']
        if constellation not in valid_constellations:
            self.errors.append(f"不支持的星座类型: {constellation}，支持的类型: {valid_constellations}")
        
        # 验证地面站数量
        ground_stations = config.get('ground_stations', 0)
        if not isinstance(ground_stations, int) or ground_stations < 1:
            self.errors.append(f"地面站数量必须是正整数，当前值: {ground_stations}")
        elif ground_stations > 30:
            self.warnings.append(f"地面站数量过多可能影响性能: {ground_stations}")
        
        # 验证带宽配置
        satellite_bandwidth = config.get('satellite_bandwidth', 0)
        if not isinstance(satellite_bandwidth, (int, float)) or satellite_bandwidth <= 0:
            self.errors.append(f"卫星带宽必须是正数，当前值: {satellite_bandwidth}")
        
        ground_bandwidth = config.get('ground_bandwidth', 0)
        if not isinstance(ground_bandwidth, (int, float)) or ground_bandwidth <= 0:
            self.errors.append(f"地面带宽必须是正数，当前值: {ground_bandwidth}")
    
    def _validate_algorithm_config(self, config: Dict[str, Any]):
        """验证算法配置"""
        algorithm_config = config.get('config', {})
        
        # 验证K值
        K = algorithm_config.get('K', 0)
        if not isinstance(K, int) or K < 1:
            self.errors.append(f"K值必须是正整数，当前值: {K}")
        elif K > 5:
            self.warnings.append(f"K值过大可能影响性能: {K}")
        
        # 验证权重参数
        r1 = algorithm_config.get('r1', 0)
        r2 = algorithm_config.get('r2', 0)
        r3 = algorithm_config.get('r3', 0)
        
        if not isinstance(r1, int) or r1 < 1:
            self.errors.append(f"r1必须是正整数，当前值: {r1}")
        if not isinstance(r2, int) or r2 < 1:
            self.errors.append(f"r2必须是正整数，当前值: {r2}")
        if not isinstance(r3, int) or r3 < 1:
            self.errors.append(f"r3必须是正整数，当前值: {r3}")
        
        # 验证权重参数关系
        if r1 >= r2:
            self.errors.append(f"r1必须小于r2，当前值: r1={r1}, r2={r2}")
        if r2 >= r3:
            self.errors.append(f"r2必须小于r3，当前值: r2={r2}, r3={r3}")
        
        # 验证阈值参数
        Ne_th = algorithm_config.get('Ne_th', 0)
        if not isinstance(Ne_th, int) or Ne_th < 1:
            self.errors.append(f"Ne_th必须是正整数，当前值: {Ne_th}")
        
        # 验证迭代次数
        max_iterations = algorithm_config.get('max_iterations', 0)
        if not isinstance(max_iterations, int) or max_iterations < 1:
            self.errors.append(f"max_iterations必须是正整数，当前值: {max_iterations}")
        elif max_iterations > 50:
            self.warnings.append(f"迭代次数过多可能影响性能: {max_iterations}")
    
    def _validate_traffic_config(self, config: Dict[str, Any]):
        """验证流量配置"""
        # 验证总流量
        total_gbps = config.get('total_gbps', 0)
        if not isinstance(total_gbps, (int, float)) or total_gbps <= 0:
            self.errors.append(f"总流量必须是正数，当前值: {total_gbps}")
        elif total_gbps > 20:
            self.warnings.append(f"总流量过大可能导致拥塞: {total_gbps}Gbps")
        
        # 验证仿真时长
        duration = config.get('duration', 0)
        if not isinstance(duration, (int, float)) or duration <= 0:
            self.errors.append(f"仿真时长必须是正数，当前值: {duration}")
        elif duration > 1000:
            self.warnings.append(f"仿真时长过长可能影响性能: {duration}秒")
        
        # 验证大象流比例
        elephant_ratio = config.get('elephant_ratio', 0)
        if not isinstance(elephant_ratio, (int, float)) or elephant_ratio < 0 or elephant_ratio > 1:
            self.errors.append(f"大象流比例必须在0-1之间，当前值: {elephant_ratio}")
        
        # 验证大象流阈值
        elephant_threshold = config.get('elephant_threshold', 0)
        if not isinstance(elephant_threshold, (int, float)) or elephant_threshold <= 0:
            self.errors.append(f"大象流阈值必须是正数，当前值: {elephant_threshold}")
    
    def _validate_output_config(self, config: Dict[str, Any]):
        """验证输出配置"""
        # 验证输出目录
        results_dir = config.get('results_dir', '')
        if not results_dir:
            self.errors.append("结果目录不能为空")
        
        log_dir = config.get('log_dir', '')
        if not log_dir:
            self.errors.append("日志目录不能为空")
        
        # 验证日志级别
        log_level = config.get('log_level', '')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if log_level not in valid_levels:
            self.errors.append(f"无效的日志级别: {log_level}，支持的级别: {valid_levels}")
    
    def _validate_directories(self, config: Dict[str, Any]):
        """验证目录是否存在或可创建"""
        results_dir = config.get('output', {}).get('results_dir', '')
        log_dir = config.get('output', {}).get('log_dir', '')
        
        for dir_name, dir_path in [('results', results_dir), ('logs', log_dir)]:
            if dir_path:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    self.errors.append(f"无法创建{dir_name}目录 {dir_path}: {e}")


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """验证配置的便捷函数"""
    validator = ConfigValidator()
    return validator.validate(config)
