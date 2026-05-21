#!/usr/bin/env python3
"""
展示 data 目录结构
"""

from pathlib import Path
from collections import defaultdict

def get_directory_structure(root_dir):
    """获取目录结构"""
    root = Path(root_dir)
    
    # 统计每个目录的文件
    dir_stats = defaultdict(lambda: {"count": 0, "size": 0, "types": defaultdict(int)})
    
    for file in root.rglob("*"):
        if file.is_file():
            parent = file.parent
            rel_parent = parent.relative_to(root)
            
            # 统计
            dir_stats[str(rel_parent)]["count"] += 1
            dir_stats[str(rel_parent)]["size"] += file.stat().st_size
            dir_stats[str(rel_parent)]["types"][file.suffix.lower()] += 1
    
    return dir_stats

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def print_structure(root_dir):
    """打印目录结构"""
    print("=" * 80)
    print(f"📁 数据目录结构: {root_dir}")
    print("=" * 80)
    print()
    
    root = Path(root_dir)
    
    # 获取所有直接子目录
    first_level_dirs = [d for d in root.iterdir() if d.is_dir()]
    
    for first_dir in sorted(first_level_dirs):
        print(f"📂 {first_dir.name}/")
        
        # 获取二级目录
        second_level_dirs = [d for d in first_dir.rglob("*") if d.is_dir()]
        
        # 统计该一级目录下的所有文件
        all_files = list(first_dir.rglob("*"))
        file_count = len([f for f in all_files if f.is_file()])
        total_size = sum(f.stat().st_size for f in all_files if f.is_file())
        
        # 统计文件类型
        file_types = defaultdict(int)
        for f in all_files:
            if f.is_file():
                file_types[f.suffix.lower()] += 1
        
        print(f"   ├─ 文件总数: {file_count}")
        print(f"   ├─ 总大小: {format_size(total_size)}")
        print(f"   ├─ 文件类型: {dict(file_types)}")
        
        # 显示二级目录
        for second_dir in sorted(second_level_dirs)[:10]:  # 最多显示10个
            rel_path = second_dir.relative_to(first_dir)
            files_in_dir = list(second_dir.glob("*"))
            file_count = len([f for f in files_in_dir if f.is_file()])
            
            if file_count > 0:
                print(f"   └─ 📂 {rel_path}/")
                print(f"       └─ 文件数: {file_count}")
        
        if len(second_level_dirs) > 10:
            print(f"   ... 还有 {len(second_level_dirs) - 10} 个子目录")
        
        print()
    
    # 显示详细统计
    print("=" * 80)
    print("📊 总体统计")
    print("=" * 80)
    
    all_files = list(root.rglob("*"))
    total_files = len([f for f in all_files if f.is_file()])
    total_size = sum(f.stat().st_size for f in all_files if f.is_file())
    
    print(f"总文件数: {total_files:,}")
    print(f"总大小: {format_size(total_size)}")
    
    # 文件类型统计
    file_types = defaultdict(lambda: {"count": 0, "size": 0})
    for f in all_files:
        if f.is_file():
            ext = f.suffix.lower()
            file_types[ext]["count"] += 1
            file_types[ext]["size"] += f.stat().st_size
    
    print("\n文件类型分布:")
    for ext, stats in sorted(file_types.items(), key=lambda x: x[1]["size"], reverse=True):
        print(f"  {ext if ext else '(无扩展名)'}: {stats['count']} 个文件, {format_size(stats['size'])}")

if __name__ == "__main__":
    data_dir = r"D:\桌面\agent\Material\data"
    print_structure(data_dir)
