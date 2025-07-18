"""
配置加载器
负责加载和合并配置文件
"""

import os
import yaml
import copy
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            # 自动检测项目根目录
            current_file = Path(__file__).resolve()
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "config"
        self.default_config_path = self.config_dir / "default_config.yaml"
        self.scenarios_dir = self.config_dir / "scenarios"
        self.current_scenario_path = self.config_dir / "current_scenario.yaml"
    
    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML格式错误 in {file_path}: {e}")
    
    def merge_config(self, base_config: Dict[str, Any], 
                    override_config: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置"""
        result = copy.deepcopy(base_config)
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return self.load_yaml(self.default_config_path)
    
    def load_scenario_config(self, scenario_name: str) -> Dict[str, Any]:
        """加载场景配置"""
        scenario_path = self.scenarios_dir / f"{scenario_name}.yaml"
        return self.load_yaml(scenario_path)
    
    def load_current_scenario(self) -> Dict[str, Any]:
        """加载当前场景配置"""
        return self.load_yaml(self.current_scenario_path)
    
    def apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        env_mappings = {
            'LDMR_CONSTELLATION': ('network', 'constellation'),
            'LDMR_GROUND_STATIONS': ('network', 'ground_stations'),
            'LDMR_TRAFFIC_GBPS': ('traffic', 'total_gbps'),
            'LDMR_DURATION': ('traffic', 'duration'),
            'LDMR_K': ('algorithm', 'config', 'K'),
            'LDMR_R3': ('algorithm', 'config', 'r3'),
            'LDMR_NE_TH': ('algorithm', 'config', 'Ne_th'),
            'LDMR_RESULTS_DIR': ('output', 'results_dir'),
            'LDMR_LOG_LEVEL': ('output', 'log_level'),
        }
        
        result = copy.deepcopy(config)
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 根据配置路径设置值
                current = result
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # 尝试转换类型
                final_key = config_path[-1]
                try:
                    if final_key in ['ground_stations', 'K', 'r3', 'Ne_th']:
                        current[final_key] = int(env_value)
                    elif final_key in ['total_gbps', 'duration']:
                        current[final_key] = float(env_value)
                    elif final_key in ['enable_statistics', 'auto_timestamp']:
                        current[final_key] = env_value.lower() in ['true', '1', 'yes']
                    else:
                        current[final_key] = env_value
                except (ValueError, TypeError):
                    # 如果转换失败，保持字符串类型
                    current[final_key] = env_value
        
        return result
    
    def load_complete_config(self, scenario: Optional[str] = None) -> Dict[str, Any]:
        """加载完整配置
        
        加载优先级：
        1. 默认配置
        2. 场景配置（如果指定）
        3. 当前场景配置（如果存在）
        4. 环境变量覆盖
        """
        # 1. 加载默认配置
        config = self.load_default_config()
        
        # 2. 应用场景配置
        if scenario:
            scenario_config = self.load_scenario_config(scenario)
            if scenario_config:
                config = self.merge_config(config, scenario_config)
        
        # 3. 应用当前场景配置
        current_config = self.load_current_scenario()
        if current_config:
            config = self.merge_config(config, current_config)
        
        # 4. 应用环境变量覆盖
        config = self.apply_env_overrides(config)
        
        return config
    
    def save_current_scenario(self, scenario_name: str):
        """保存当前场景配置"""
        scenario_config = self.load_scenario_config(scenario_name)
        if scenario_config:
            with open(self.current_scenario_path, 'w', encoding='utf-8') as f:
                yaml.dump(scenario_config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
    
    def list_available_scenarios(self) -> List[str]:
        """列出可用的场景"""
        scenarios = []
        if self.scenarios_dir.exists():
            for file_path in self.scenarios_dir.glob("*.yaml"):
                scenarios.append(file_path.stem)
        return sorted(scenarios)


# 全局配置加载器实例
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """获取全局配置加载器实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def load_default_config() -> Dict[str, Any]:
    """加载默认配置的便捷函数"""
    return get_config_loader().load_complete_config()

def load_scenario_config(scenario_name: str) -> Dict[str, Any]:
    """加载场景配置的便捷函数"""
    return get_config_loader().load_complete_config(scenario_name)

def switch_scenario(scenario_name: str) -> Dict[str, Any]:
    """切换到指定场景"""
    loader = get_config_loader()
    loader.save_current_scenario(scenario_name)
    return loader.load_complete_config()
