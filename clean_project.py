#!/usr/bin/env python3
"""
项目清理脚本
清理缓存文件和临时文件
"""

import os
import shutil
from pathlib import Path


def clean_pycache(root_dir="."):
    """清理__pycache__目录"""
    removed_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"✅ 已删除: {pycache_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ 删除失败 {pycache_path}: {e}")
    
    return removed_count


def clean_ds_store(root_dir="."):
    """清理.DS_Store文件"""
    removed_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file == '.DS_Store':
                ds_store_path = os.path.join(root, file)
                try:
                    os.remove(ds_store_path)
                    print(f"✅ 已删除: {ds_store_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ 删除失败 {ds_store_path}: {e}")
    
    return removed_count


def clean_temp_files(root_dir="."):
    """清理临时文件"""
    temp_extensions = ['.tmp', '.bak', '.orig', '.pyc', '.pyo']
    removed_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if any(file.endswith(ext) for ext in temp_extensions):
                temp_path = os.path.join(root, file)
                try:
                    os.remove(temp_path)
                    print(f"✅ 已删除: {temp_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ 删除失败 {temp_path}: {e}")
    
    return removed_count


def main():
    """主清理函数"""
    print("🧹 开始清理项目文件...")
    print("=" * 50)
    
    # 清理__pycache__
    print("🗂️  清理 __pycache__ 目录...")
    pycache_count = clean_pycache()
    print(f"   清理了 {pycache_count} 个 __pycache__ 目录")
    
    # 清理.DS_Store
    print("\n🍎 清理 .DS_Store 文件...")
    ds_store_count = clean_ds_store()
    print(f"   清理了 {ds_store_count} 个 .DS_Store 文件")
    
    # 清理临时文件
    print("\n🗑️  清理临时文件...")
    temp_count = clean_temp_files()
    print(f"   清理了 {temp_count} 个临时文件")
    
    print("\n" + "=" * 50)
    total_cleaned = pycache_count + ds_store_count + temp_count
    print(f"✅ 清理完成！总共清理了 {total_cleaned} 个文件/目录")
    
    if total_cleaned == 0:
        print("🎉 项目已经很干净了！")


if __name__ == "__main__":
    main()
