#!/usr/bin/env python3
"""
LDMR算法标准仿真
简化版主程序 - 直接运行标准LDMR算法
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir / 'src'))

from config import load_default_config
from runner import LDMRRunner, setup_logger
from runner.logger import log_exception


def main():
    """
    简化的主函数 - 只执行标准LDMR仿真
    """
    try:
        # 1. 加载配置
        config = load_default_config()
        
        # 2. 设置日志
        logger = setup_logger(config.get('output', {}))
        
        # 3. 创建LDMR运行器
        runner = LDMRRunner(config)
        
        # 4. 运行仿真
        results = runner.run()
        
        # 5. 返回结果（如果需要）
        return results
        
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
        sys.exit(1)
    except Exception as e:
        if 'logger' in locals():
            log_exception(logger, e, "主程序")
        else:
            print(f"❌ 程序发生异常: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
