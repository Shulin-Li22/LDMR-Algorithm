# LDMR算法仿真

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

基于论文《A GNN-Enabled Multipath Routing Algorithm for Spatial-Temporal Varying LEO Satellite Networks》的LDMR (Link Disjoint Multipath Routing) 算法完整实现。

## 🎯 项目简介

本项目实现了面向LEO卫星网络的链路不相交多路径路由算法，主要特色：

- **完整的LDMR算法实现**：严格按照论文Algorithm 1实现
- **多星座网络支持**：GlobalStar、Iridium等预定义星座
- **基准算法对比**：SPF、ECMP等基准算法完整实现
- **灵活的配置系统**：支持多场景配置和参数调优
- **详细的性能分析**：路径不相交性验证、统计分析等
- **结果导出和可视化**：CSV数据导出、图表生成

## 🚀 快速开始

### 环境要求

- Python 3.8+
- NumPy >= 1.21.0
- NetworkX >= 2.8.0
- Matplotlib >= 3.5.0
- PyYAML >= 6.0

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/Shulin-Li22/LDMR-Algorithm.git
cd ldmr-simulation

# 安装依赖
pip install -r requirements.txt
```

### 快速运行

```bash
python main.py
```

## 📁 项目结构

```
ldmr_simulation/
├── README.md                   # 项目说明文档
├── requirements.txt            # 依赖清单
├── main.py                     # 完整版主程序
├── config.py                   # 配置管理
├── benchmark.py                # 基准测试
├── param_analysis.py           # 参数分析
├── config/                     # 配置文件目录
│   ├── default.yaml            # 默认配置
│   └── scenarios/              # 场景配置
│       ├── testing.yaml        # 测试场景
│       ├── light_load.yaml     # 轻负载场景
│       ├── heavy_load.yaml     # 重负载场景
│       └── performance.yaml    # 性能测试场景
├── src/                        # 核心源代码
│   ├── algorithms/             # 算法模块
│   │   ├── ldmr_algorithms.py  # LDMR核心算法 ⭐
│   │   ├── basic_algorithms.py # 基础算法
│   │   └── baseline/           # 基准算法
│   ├── topology/               # 拓扑模块
│   │   ├── topology_base.py    # 基础拓扑类
│   │   └── satellite_constellation.py # 卫星星座
│   ├── traffic/                # 流量模块
│   │   └── traffic_model.py    # 流量生成模型
│   └── output/                 # 输出模块
│       ├── result_exporter.py  # 结果导出
│       └── visualizer.py       # 可视化生成
├── results/                    # 结果输出
│   ├── data/                   # CSV数据文件
│   └── figures/                # 图表文件
└── logs/                       # 日志文件
```

## ⚙️ 配置说明

### 基础配置

编辑 `config/default.yaml` 来修改默认参数：

```yaml
# 网络配置
network:
  constellation: "globalstar"    # 星座类型: globalstar, iridium
  ground_stations: 10           # 地面站数量
  satellite_bandwidth: 10.0     # 卫星链路带宽 (Gbps)
  ground_bandwidth: 5.0         # 地面链路带宽 (Gbps)

# LDMR算法配置
algorithm:
  K: 2                          # 每个节点对的路径数量
  r1: 1                         # 权重下界1
  r2: 10                        # 权重下界2
  r3: 50                        # 权重上界
  Ne_th: 2                      # 链路利用频次阈值

# 流量配置
traffic:
  total_gbps: 6.0               # 总流量 (Gbps)
  duration: 180.0               # 仿真时长 (秒)
  elephant_ratio: 0.3           # 大象流比例

# 输出配置
output:
  enable_export: true           # 启用结果导出
  export_csv: true              # 导出CSV数据
  export_figures: true          # 生成图表
```

### 场景配置

项目提供了多种预定义场景：

- **testing.yaml**: 测试场景（小规模快速测试）
- **light_load.yaml**: 轻负载场景
- **heavy_load.yaml**: 重负载场景（测试拥塞处理）
- **performance.yaml**: 性能测试场景（Iridium星座）

## 🎮 使用方法

### 1. 主程序

```bash
python main.py
```

提供四个核心功能：
1. 🚀 运行LDMR算法
2. 📊 基准算法对比
3. 🔬 参数敏感性分析
4. 🔄 切换场景配置

### 2. 单独运行各模块

```bash
# 运行基准测试
python benchmark.py

# 运行参数分析
python param_analysis.py
```

### 3. 场景切换

```bash
# 查看可用场景
python -c "from config import list_scenarios; print(list_scenarios())"

# 切换到性能测试场景
python -c "from config import load_scenario; config = load_scenario('performance')"
```

## 📊 性能评估

### 关键指标

- **成功率**：成功计算路径的流量需求比例
- **平均延迟**：所有路径的平均端到端延迟
- **路径不相交率**：链路不相交路径的比例
- **计算时间**：算法执行时间
- **吞吐量**：网络传输能力

### 基准算法对比

| 算法 | 成功率 | 平均延迟(ms) | 平均路径数 | 执行时间(s) |
|------|--------|----------|-------|---------|
| LDMR | 100.0% | 183.78   | 2.0   | 2.62    |
| SPF  | 100.0% | 141.88   | 1.0   | 0.43    |
| ECMP | 100.0% | 160.00   | 2.0   | 6.49    |


## 🔬 算法实现细节

### LDMR核心算法

本项目严格按照论文Algorithm 1实现：

1. **初始化阶段**：重置权重矩阵和链路使用计数
2. **最短路径计算**：为所有节点对计算最短延迟路径
3. **多路径计算**：按流量大小降序处理每个需求
4. **权重动态更新**：根据链路使用频次调整权重
5. **备用路径搜索**：寻找链路不相交的备用路径

### 关键特性

- **链路不相交性**：确保多条路径之间没有共享链路
- **动态权重更新**：避免路径冲突和负载不均
- **流量优先级**：优先处理大流量请求
- **拓扑适应性**：支持时变卫星网络拓扑

## 📈 结果输出

### 自动导出功能

运行仿真后，系统会自动生成：

1. **CSV数据文件**：详细的数值结果
   - `ldmr_results_YYYYMMDD_HHMMSS.csv`
   - `benchmark_comparison_YYYYMMDD_HHMMSS.csv`

2. **可视化图表**：
   - 算法性能对比图
   - 参数敏感性分析图
   - 路径分析图表
   - 性能趋势图

3. **摘要报告**：
   - `experiment_summary_YYYYMMDD_HHMMSS.txt`

### 结果文件位置

```
results/
├── data/                       # CSV数据文件
│   ├── ldmr_results_*.csv
│   ├── benchmark_comparison_*.csv
│   └── experiment_summary_*.txt
└── figures/                    # 图表文件
    ├── algorithm_comparison_*.png
    ├── parameter_sensitivity_*.png
    ├── path_analysis_*.png
    └── performance_trends_*.png
```

## 📚 文档和资源

### 论文引用

如果您在研究中使用了本项目，请引用原始论文：

```bibtex
@article{huang2024gnn,
  title={A GNN-Enabled Multipath Routing Algorithm for Spatial-Temporal Varying LEO Satellite Networks},
  author={Huang, Yunxue and Yang, Dong and Feng, Bohao and others},
  journal={IEEE Transactions on Vehicular Technology},
  volume={73},
  number={4},
  pages={5454--5468},
  year={2024},
  publisher={IEEE}
}
```

### 相关资源
- [论文PDF](https://ieeexplore.ieee.org/document/10321744)
- [技术文档](technical_doc.md)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！



## 🐛 问题排查

### 常见问题

1. **导入模块失败**
   ```bash
   # 确保项目路径正确
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **配置文件不存在**
   ```bash
   # 检查配置文件
   ls config/default.yaml
   ```

3. **依赖包缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

### 性能调优

- 减少流量规模以加快测试速度
- 调整参数 `r3` 和 `Ne_th` 优化性能
- 使用较小的星座配置进行调试

## 📌 声明

本项目的部分代码由 GenAI 辅助生成（ChatGPT, Gemini, Claude），并由作者进行审查、修改和完善。
请在使用或参考本项目代码时，自行核实其正确性与适用性，必要时进行适当的测试和调整。

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢原论文作者提供的优秀算法设计
- 感谢开源社区提供的基础工具和库
- 感谢所有为项目改进做出贡献的开发者

## 🌟 Star支持

如果这个项目对您有帮助，请给我们一个Star！这是对我们最大的鼓励和支持。

---

**最后更新**: 2025年8月7日
**项目状态**: 稳定版本 v2.1.0
