"""
基准算法模块
实现SPF、ECMP等基准算法用于性能对比
"""

from .spf_algorithm import SPFAlgorithm
from .ecmp_algorithm import ECMPAlgorithm
from .baseline_interface import BaselineAlgorithm, AlgorithmResult
from .benchmark_manager import BenchmarkManager, run_quick_benchmark

__all__ = ['SPFAlgorithm', 'ECMPAlgorithm', 'BaselineAlgorithm', 'AlgorithmResult', 'BenchmarkManager', 'run_quick_benchmark']
