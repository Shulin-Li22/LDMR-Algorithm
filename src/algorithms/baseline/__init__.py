"""
基准算法模块
实现SPF、ECMP等基准算法用于性能对比
"""

from .spf_algorithm import SPFAlgorithm
from .ecmp_algorithm import ECMPAlgorithm
from .baseline_interface import BaselineAlgorithm, AlgorithmResult

__all__ = ['SPFAlgorithm', 'ECMPAlgorithm', 'BaselineAlgorithm', 'AlgorithmResult']
