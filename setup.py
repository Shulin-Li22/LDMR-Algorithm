#!/usr/bin/env python3
"""
LDMR算法仿真系统安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "LDMR (Link Disjoint Multipath Routing) Algorithm Implementation for LEO Satellite Networks"

# 读取requirements文件
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="ldmr-simulation",
    version="1.0.0",
    description="LDMR Algorithm Implementation for LEO Satellite Networks",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/ldmr-simulation",
    
    # 包配置
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # 依赖配置
    install_requires=read_requirements(),
    python_requires=">=3.8",
    
    # 分类信息
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    
    # 关键词
    keywords="satellite networks, routing algorithms, LEO, multipath routing",
    
    # 入口点
    entry_points={
        'console_scripts': [
            'ldmr-sim=main_simple:main',
            'ldmr-benchmark=scripts.benchmark:main',
        ],
    },
    
    # 包含额外文件
    include_package_data=True,
    package_data={
        '': ['*.yaml', '*.yml', '*.txt', '*.md'],
    },
    
    # 额外配置
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
        ],
        'visualization': [
            'jupyter>=1.0',
            'ipywidgets>=7.0',
        ],
    },
    
    # 项目URL
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/ldmr-simulation/issues',
        'Source': 'https://github.com/yourusername/ldmr-simulation',
        'Documentation': 'https://github.com/yourusername/ldmr-simulation/wiki',
    },
)
