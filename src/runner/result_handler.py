"""
结果处理器
负责保存和管理仿真结果
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from runner.logger import get_logger


class ResultHandler:
    """结果处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger()
        self.output_config = config['output']
        self.results_dir = Path(self.output_config['results_dir'])
        self.auto_timestamp = self.output_config.get('auto_timestamp', True)
        
        # 确保结果目录存在
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, base_name: str = "ldmr_results") -> str:
        """生成文件名"""
        if self.auto_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{base_name}_{timestamp}.json"
        else:
            return f"{base_name}.json"
    
    def _clean_results_for_json(self, data: Any) -> Any:
        """清理数据以便JSON序列化"""
        if isinstance(data, dict):
            return {str(k): self._clean_results_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_results_for_json(item) for item in data]
        elif isinstance(data, tuple):
            return list(data)
        elif hasattr(data, '__dict__'):
            return str(data)
        else:
            return data
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """保存结果到JSON文件"""
        try:
            # 生成文件名
            filename = self._generate_filename()
            filepath = self.results_dir / filename
            
            # 清理数据
            clean_results = self._clean_results_for_json(results)
            
            # 保存到JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(clean_results, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"💾 结果已保存到: {filepath}")
            
            # 可选：保存简要摘要
            if self.output_config.get('save_summary', True):
                self._save_summary(results, filepath.with_suffix('.summary.txt'))
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
            raise
    
    def _save_summary(self, results: Dict[str, Any], summary_path: Path):
        """保存简要摘要"""
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_summary_text(results))
            
            self.logger.info(f"📋 摘要已保存到: {summary_path}")
            
        except Exception as e:
            self.logger.warning(f"保存摘要失败: {e}")
    
    def _generate_summary_text(self, results: Dict[str, Any]) -> str:
        """生成摘要文本"""
        config = results.get('simulation_config', {})
        stats = results.get('ldmr_statistics', {})
        disjoint = results.get('disjoint_verification', {})
        
        summary = f"""LDMR算法仿真结果摘要
==========================================

仿真信息:
- 仿真名称: {config.get('name', 'N/A')}
- 会话ID: {results.get('session_id', 'N/A')}
- 时间戳: {results.get('timestamp', 'N/A')}

网络配置:
- 星座类型: {config.get('constellation', 'N/A')}
- 地面站数: {config.get('ground_stations', 'N/A')}
- 总流量: {config.get('total_traffic', 'N/A')} Gbps
- 仿真时长: {config.get('duration', 'N/A')} 秒

LDMR性能:
- 成功率: {stats.get('success_rate', 0):.2%}
- 平均延迟: {stats.get('avg_path_delay', 0):.3f} ms
- 最小延迟: {stats.get('min_path_delay', 0):.3f} ms
- 最大延迟: {stats.get('max_path_delay', 0):.3f} ms
- 总路径数: {stats.get('total_paths_calculated', 0)}
- 平均路径长度: {stats.get('avg_path_length', 0):.1f} 跳
- 总计算时间: {stats.get('total_computation_time', 0):.2f} 秒
- 平均计算时间: {stats.get('avg_computation_time', 0):.4f} 秒

路径不相交性:
- 不相交路径数: {disjoint.get('disjoint_results', 0)}
- 冲突路径数: {disjoint.get('non_disjoint_results', 0)}
- 不相交率: {disjoint.get('disjoint_rate', 0):.2%}

算法执行统计:
- 总执行时间: {stats.get('algorithm_execution_stats', {}).get('total_time', 0):.2f} 秒
- 路径计算次数: {stats.get('algorithm_execution_stats', {}).get('path_calculations', 0)}
- 权重更新次数: {stats.get('algorithm_execution_stats', {}).get('weight_updates', 0)}
- 链路移除次数: {stats.get('algorithm_execution_stats', {}).get('link_removals', 0)}

仿真总时间: {results.get('simulation_time', 0):.2f} 秒
==========================================
"""
        return summary
    
    def load_results(self, filepath: str) -> Dict[str, Any]:
        """加载结果文件"""
        try:
            filepath = Path(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            self.logger.info(f"📂 结果已加载: {filepath}")
            return results
            
        except Exception as e:
            self.logger.error(f"加载结果失败: {e}")
            raise
    
    def list_result_files(self) -> list:
        """列出所有结果文件"""
        try:
            result_files = []
            for file_path in self.results_dir.glob("*.json"):
                if file_path.stem.startswith("ldmr_results"):
                    result_files.append(str(file_path))
            
            return sorted(result_files, reverse=True)  # 按时间倒序
            
        except Exception as e:
            self.logger.error(f"列出结果文件失败: {e}")
            return []
    
    def get_latest_result(self) -> str:
        """获取最新的结果文件"""
        result_files = self.list_result_files()
        if result_files:
            return result_files[0]
        else:
            raise FileNotFoundError("没有找到结果文件")
    
    def cleanup_old_results(self, keep_count: int = 10):
        """清理旧的结果文件，保留最新的几个"""
        try:
            result_files = self.list_result_files()
            
            if len(result_files) > keep_count:
                files_to_remove = result_files[keep_count:]
                
                for file_path in files_to_remove:
                    os.remove(file_path)
                    # 同时删除对应的摘要文件
                    summary_path = Path(file_path).with_suffix('.summary.txt')
                    if summary_path.exists():
                        os.remove(summary_path)
                
                self.logger.info(f"🗑️  清理了 {len(files_to_remove)} 个旧结果文件")
                
        except Exception as e:
            self.logger.error(f"清理旧结果失败: {e}")
