# LDMR算法仿真系统

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)

基于论文《A GNN-Enabled Multipath Routing Algorithm for Spatial-Temporal Varying LEO Satellite Networks》的LDMR (Link Disjoint Multipath Routing) 算法完整实现。

## 🎯 项目简介

本项目实现了面向LEO卫星网络的链路不相交多路径路由算法，主要特色：

- ✅ **完整的LDMR算法实现**：严格按照论文Algorithm 1实现
- ✅ **多星座网络支持**：GlobalStar、Iridium等预定义星座
- ✅ **基准算法对比**：SPF、ECMP等基准算法完整实现
- ✅ **灵活的配置系统**：支持多场景配置和参数调优
- ✅ **详细的性能分析**：路径不相交性验证、统计分析等
- ✅ **可视化支持**：结果可视化和报告生成

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/ldmr-simulation.git
cd ldmr-simulation

# 安装依赖
pip install -r requirements.txt
```

### 运行仿真

```bash
# 标准LDMR仿真
python main_simple.py

# 运行基准测试
python scripts/benchmark.py
```

### 输出示例

```
🚀 LDMR算法仿真开始...
   仿真名称: LDMR Standard Simulation
🔧 构建网络拓扑...
   网络构建完成: 58节点, 116链路
📈 生成流量需求...
   流量生成完成: 6003个需求
⚡ 运行LDMR算法...
   LDMR算法完成: 成功率=100.00%
✅ LDMR仿真完成!

============================================================
📋 LDMR仿真结果摘要
============================================================
📊 成功率: 100.00%
⏱️  平均延迟: 0.073ms
🔗 总路径数: 12006
🚀 计算时间: 2.24s
✅ 路径不相交率: 100.00%
============================================================
```

## 📁 项目结构

```
ldmr_simulation/
├── README.md                   # 项目说明文档
├── requirements.txt            # 依赖清单
├── setup.py                    # 安装脚本
├── main_simple.py              # 简化版主程序
├── config/                     # 配置文件目录
│   ├── default_config.yaml     # 默认配置
│   └── scenarios/              # 场景配置
│       ├── testing.yaml        # 测试场景
│       ├── light_load.yaml     # 轻负载场景
│       ├── heavy_load.yaml     # 重负载场景
│       └── performance.yaml    # 性能测试场景
├── src/                        # 核心源代码
│   ├── algorithms/             # 算法模块
│   │   ├── ldmr_algorithms.py  # LDMR核心算法
│   │   ├── basic_algorithms.py # 基础算法
│   │   └── baseline/           # 基准算法
│   ├── topology/               # 拓扑模块
│   │   ├── topology_base.py    # 基础拓扑类
│   │   └── satellite_constellation.py # 卫星星座
│   ├── traffic/                # 流量模块
│   │   └── traffic_model.py    # 流量生成模型
│   ├── config/                 # 配置管理
│   └── runner/                 # 运行器
├── scripts/                    # 工具脚本
│   ├── benchmark.py            # 基准测试
│   └── advanced_test.py        # 高级功能测试
├── results/                    # 结果输出
└── logs/                       # 日志文件
```

## ⚙️ 配置说明

### 基础配置

编辑 `config/default_config.yaml` 来修改默认参数：

```yaml
# 网络配置
network:
  constellation: "globalstar"    # 星座类型
  ground_stations: 10           # 地面站数量
  satellite_bandwidth: 10.0     # 卫星链路带宽 (Gbps)

# LDMR算法配置
algorithm:
  config:
    K: 2                        # 每个节点对的路径数量
    r3: 50                      # 权重上界
    Ne_th: 2                    # 链路利用频次阈值

# 流量配置
traffic:
  total_gbps: 6.0               # 总流量 (Gbps)
  duration: 180.0               # 仿真时长 (秒)
```

### 场景切换

```bash
# 使用场景管理器切换
python scripts/scenario_manager.py switch performance

# 或通过环境变量覆盖
export LDMR_TRAFFIC_GBPS=8.0
export LDMR_GROUND_STATIONS=15
python main_simple.py
```

## 📊 性能评估

### 单场景测试

```bash
# 标准性能测试
python main_simple.py

# 重负载测试
python scripts/scenario_manager.py switch heavy_load
python main_simple.py
```

### 基准算法对比

```bash
# 交互式基准测试
python scripts/benchmark.py

# 多场景基准测试
python scripts/benchmark.py multi

# 算法详细对比
python scripts/benchmark.py compare
```

### 参数敏感性分析

```bash
# r3参数分析
python scripts/advanced_test.py param-analysis r3

# K参数分析
python scripts/advanced_test.py param-analysis K
```

## 📈 关键指标

### LDMR算法指标

- **成功率**：成功计算路径的流量需求比例
- **平均延迟**：所有路径的平均端到端延迟
- **路径不相交率**：链路不相交路径的比例
- **计算时间**：算法执行时间

### 对比基准

| 算法 | 成功率 | 平均延迟(ms) | 平均路径数 | 执行时间(s) |
|------|--------|-------------|-----------|------------|
| LDMR | 100.0% | 0.073       | 2.0       | 2.24       |
| SPF  | 100.0% | 0.076       | 1.0       | 0.45       |
| ECMP | 100.0% | 0.074       | 3.2       | 1.12       |

## 🔬 算法实现细节

### LDMR核心算法

本项目严格按照论文Algorithm 1实现：

1. **初始化阶段**：重置权重矩阵和链路使用计数
2. **最短路径计算**：为所有节点对计算最短延迟路径
3. **多路径计算**：按流量大小降序处理每个需求
4. **权重动态更新**：根据链路使用频次调整权重
5. **备用路径搜索**：寻找链路不相交的备用路径

### 关键参数

- **K=2**：论文验证的最优路径数量
- **r3=50**：论文测试结果显示的最优权重上界
- **Ne_th=2**：链路利用频次阈值

## 🧪 测试验证

### 完整验证

```bash
# 运行所有测试场景
python scripts/advanced_test.py multi-scenario

# 验证路径不相交性
python scripts/advanced_test.py verify-disjoint
```

## 📝 引用

如果您在研究中使用了本项目，请引用原始论文：

```bibtex
@article{ldmr2024,
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

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/yourusername/ldmr-simulation.git
cd ldmr-simulation

# 安装开发依赖
pip install -e ".[dev]"

# 运行代码格式化
black src/ scripts/

# 运行测试
pytest tests/
```

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢原论文作者提供的优秀算法设计
- 感谢开源社区提供的基础工具和库
- 感谢所有为项目改进做出贡献的开发者

## 📞 联系方式

- 项目主页：[https://github.com/yourusername/ldmr-simulation](https://github.com/yourusername/ldmr-simulation)
- 问题反馈：[Issues](https://github.com/yourusername/ldmr-simulation/issues)
- 邮箱：your.email@example.com

---

**🌟 如果这个项目对您有帮助，请给我们一个Star！**
