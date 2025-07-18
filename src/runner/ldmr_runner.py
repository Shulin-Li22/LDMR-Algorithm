"""
LDMR运行器
负责执行标准LDMR算法仿真
"""

import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from topology.satellite_constellation import LEONetworkBuilder
from traffic.traffic_model import TrafficGenerator
from algorithms.ldmr_algorithms import LDMRAlgorithm, LDMRConfig, run_ldmr_simulation
from config.validator import validate_config
from runner.result_handler import ResultHandler
from runner.logger import get_logger


class LDMRRunner:
    """LDMR算法运行器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger()
        self.result_handler = ResultHandler(config)
        self.start_time = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 验证配置
        self._validate_config()
        
        # 确保输出目录存在
        self._ensure_output_directories()
    
    def _validate_config(self):
        """验证配置"""
        is_valid, errors, warnings = validate_config(self.config)
        
        if warnings:
            for warning in warnings:
                self.logger.warning(warning)
        
        if not is_valid:
            self.logger.error("配置验证失败:")
            for error in errors:
                self.logger.error(f"  - {error}")
            raise ValueError("配置验证失败")
    
    def _ensure_output_directories(self):
        """确保输出目录存在"""
        results_dir = self.config['output']['results_dir']
        log_dir = self.config['output']['log_dir']
        
        for directory in [results_dir, log_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def _create_network_topology(self):
        """创建网络拓扑"""
        self.logger.info("🔧 构建网络拓扑...")
        
        network_config = self.config['network']
        constellation = network_config['constellation']
        num_ground_stations = network_config['ground_stations']
        satellite_bandwidth = network_config['satellite_bandwidth']
        ground_bandwidth = network_config['ground_bandwidth']
        
        # 创建网络构建器
        builder = LEONetworkBuilder(constellation, num_ground_stations)
        
        # 构建网络
        topology = builder.build_network(
            satellite_bandwidth=satellite_bandwidth,
            ground_bandwidth=ground_bandwidth
        )
        
        # 获取网络统计信息
        network_stats = topology.get_statistics()
        
        self.logger.info(f"   网络构建完成: {network_stats['total_nodes']}节点, "
                        f"{network_stats['total_links']}链路")
        
        if not network_stats['is_connected']:
            self.logger.warning("   ⚠️  网络未完全连通")
        
        return topology, network_stats
    
    def _generate_traffic_demands(self, topology):
        """生成流量需求"""
        self.logger.info("📈 生成流量需求...")
        
        traffic_config = self.config['traffic']
        traffic_gen_config = self.config['traffic_generation']
        
        # 获取地面站列表
        ground_stations = [
            node.id for node in topology.nodes.values()
            if node.type.value == 'ground_station'
        ]
        
        # 创建流量生成器
        generator = TrafficGenerator()
        
        # 生成流量需求
        demands = generator.generate_traffic_demands(
            ground_station_ids=ground_stations,
            total_traffic=traffic_config['total_gbps'],
            duration=traffic_config['duration'],
            elephant_ratio=traffic_config['elephant_ratio']
        )
        
        # 获取流量统计信息
        traffic_stats = generator.get_flow_statistics(demands)
        
        self.logger.info(f"   流量生成完成: {len(demands)}个需求")
        self.logger.info(f"   大象流: {traffic_stats['elephant_flows']}个, "
                        f"老鼠流: {traffic_stats['mouse_flows']}个")
        
        return demands, traffic_stats
    
    def _create_ldmr_algorithm(self):
        """创建LDMR算法实例"""
        algorithm_config = self.config['algorithm']['config']
        
        # 创建LDMR配置
        ldmr_config = LDMRConfig(
            K=algorithm_config['K'],
            r1=algorithm_config['r1'],
            r2=algorithm_config['r2'],
            r3=algorithm_config['r3'],
            Ne_th=algorithm_config['Ne_th'],
            max_iterations=algorithm_config['max_iterations'],
            enable_statistics=algorithm_config['enable_statistics']
        )
        
        return LDMRAlgorithm(ldmr_config)
    
    def _run_ldmr_algorithm(self, topology, demands):
        """运行LDMR算法"""
        self.logger.info("⚡ 运行LDMR算法...")
        
        # 创建LDMR算法实例
        ldmr = self._create_ldmr_algorithm()
        
        # 运行算法
        results = ldmr.run_ldmr_algorithm(topology, demands)
        
        # 获取统计信息
        statistics = ldmr.get_algorithm_statistics(results)
        
        # 验证路径不相交性
        disjoint_stats = ldmr.verify_path_disjointness(results)
        
        self.logger.info(f"   LDMR算法完成: 成功率={statistics.get('success_rate', 0):.2%}")
        self.logger.info(f"   平均延迟: {statistics.get('avg_path_delay', 0):.3f}ms")
        self.logger.info(f"   路径不相交率: {disjoint_stats.get('disjoint_rate', 0):.2%}")
        
        return results, statistics, disjoint_stats
    
    def _create_simulation_results(self, network_stats, traffic_stats, 
                                  ldmr_results, ldmr_statistics, disjoint_stats):
        """创建仿真结果"""
        simulation_time = time.time() - self.start_time
        
        results = {
            'session_id': self.session_id,
            'simulation_config': {
                'name': self.config['simulation']['name'],
                'constellation': self.config['network']['constellation'],
                'ground_stations': self.config['network']['ground_stations'],
                'total_traffic': self.config['traffic']['total_gbps'],
                'duration': self.config['traffic']['duration'],
                'algorithm': self.config['algorithm']['name'],
                'algorithm_config': self.config['algorithm']['config']
            },
            'network_stats': network_stats,
            'traffic_stats': traffic_stats,
            'ldmr_statistics': ldmr_statistics,
            'disjoint_verification': disjoint_stats,
            'simulation_time': simulation_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # 如果启用了详细路径保存
        if self.config['output']['save_detailed_paths']:
            results['detailed_paths'] = [
                {
                    'source': result.source_id,
                    'destination': result.destination_id,
                    'paths': [
                        {
                            'nodes': path.nodes,
                            'delay': path.total_delay,
                            'hops': path.length
                        }
                        for path in result.paths
                    ]
                }
                for result in ldmr_results
            ]
        
        return results
    
    def run(self) -> Dict[str, Any]:
        """运行标准LDMR仿真"""
        self.start_time = time.time()
        
        try:
            self.logger.info("🚀 LDMR算法仿真开始...")
            self.logger.info(f"   仿真名称: {self.config['simulation']['name']}")
            
            # 1. 创建网络拓扑
            topology, network_stats = self._create_network_topology()
            
            # 2. 生成流量需求
            demands, traffic_stats = self._generate_traffic_demands(topology)
            
            # 3. 运行LDMR算法
            ldmr_results, ldmr_statistics, disjoint_stats = self._run_ldmr_algorithm(
                topology, demands)
            
            # 4. 创建仿真结果
            results = self._create_simulation_results(
                network_stats, traffic_stats, ldmr_results, 
                ldmr_statistics, disjoint_stats
            )
            
            # 5. 保存结果
            result_file = self.result_handler.save_results(results)
            
            # 6. 显示摘要
            self._display_summary(results, result_file)
            
            self.logger.info("✅ LDMR仿真完成!")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 仿真失败: {e}")
            raise
    
    def _display_summary(self, results: Dict[str, Any], result_file: str):
        """显示仿真摘要"""
        stats = results['ldmr_statistics']
        disjoint = results['disjoint_verification']
        
        print("\n" + "="*60)
        print("📋 LDMR仿真结果摘要")
        print("="*60)
        print(f"📊 成功率: {stats.get('success_rate', 0):.2%}")
        print(f"⏱️  平均延迟: {stats.get('avg_path_delay', 0):.3f}ms")
        print(f"🔗 总路径数: {stats.get('total_paths_calculated', 0)}")
        print(f"🚀 计算时间: {stats.get('total_computation_time', 0):.2f}s")
        print(f"✅ 路径不相交率: {disjoint.get('disjoint_rate', 0):.2%}")
        print(f"💾 结果文件: {result_file}")
        print("="*60)
