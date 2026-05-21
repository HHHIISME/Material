#!/usr/bin/env python3
"""
GraphRAG 进度监控脚本
每隔 30 秒显示一次处理进度
"""

import time
import os
from pathlib import Path
from datetime import datetime

def get_latest_log_file(log_dir):
    """获取最新的日志文件"""
    log_files = list(Path(log_dir).glob("*.log"))
    if not log_files:
        return None
    return max(log_files, key=lambda f: f.stat().st_mtime)

def parse_progress_from_log(log_file):
    """从日志文件解析进度"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_progress = 0
        total = 548  # 默认值
        current_stage = "未知"
        errors = []
        
        for line in lines[-100:]:  # 只看最后 100 行
            # 解析进度
            if "extract graph progress:" in line:
                parts = line.split("extract graph progress:")
                if len(parts) > 1:
                    progress_str = parts[1].strip().split()[0]
                    try:
                        current_progress = int(progress_str)
                    except:
                        pass
                current_stage = "实体提取"
            
            # 解析错误
            if "Error" in line or "Exception" in line or "错误" in line:
                errors.append(line.strip()[:100])
            
            # 解析阶段
            if "Starting workflow:" in line:
                current_stage = line.split("Starting workflow:")[1].strip()
            if "Workflow completed:" in line:
                current_stage = f"✅ {line.split('Workflow completed:')[1].strip()}"
        
        return {
            "progress": current_progress,
            "total": total,
            "stage": current_stage,
            "errors": errors[-3:] if errors else []  # 最近 3 个错误
        }
    except Exception as e:
        return {"error": str(e)}

def get_output_stats(output_dir):
    """获取输出文件统计"""
    stats = {}
    
    try:
        entities_path = Path(output_dir) / "entities.parquet"
        if entities_path.exists():
            import pandas as pd
            df = pd.read_parquet(entities_path)
            stats["entities"] = len(df)
    except:
        stats["entities"] = 0
    
    try:
        relationships_path = Path(output_dir) / "relationships.parquet"
        if relationships_path.exists():
            import pandas as pd
            df = pd.read_parquet(relationships_path)
            stats["relationships"] = len(df)
    except:
        stats["relationships"] = 0
    
    return stats

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    graphrag_dir = r"D:\桌面\agent\Material\KnowledgeGraph\KnowledgeGraph\graphrag"
    log_dir = os.path.join(graphrag_dir, "logs")
    output_dir = os.path.join(graphrag_dir, "output")
    
    print("=" * 60)
    print("📊 GraphRAG 进度监控")
    print("=" * 60)
    print(f"监控目录: {graphrag_dir}")
    print(f"刷新间隔: 30 秒")
    print("按 Ctrl+C 退出监控")
    print("=" * 60)
    
    prev_progress = 0
    
    try:
        while True:
            # 获取日志文件
            log_file = get_latest_log_file(log_dir)
            
            if log_file:
                # 解析进度
                result = parse_progress_from_log(log_file)
                
                # 获取输出统计
                stats = get_output_stats(output_dir)
                
                # 清屏并显示
                clear_screen()
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("=" * 60)
                print(f"📊 GraphRAG 进度监控 - {now}")
                print("=" * 60)
                
                if "error" in result:
                    print(f"❌ 错误: {result['error']}")
                else:
                    progress = result["progress"]
                    total = result["total"]
                    percent = (progress / total * 100) if total > 0 else 0
                    
                    # 进度条
                    bar_length = 40
                    filled = int(bar_length * progress / total) if total > 0 else 0
                    bar = "█" * filled + "░" * (bar_length - filled)
                    
                    print(f"\n🔄 当前阶段: {result['stage']}")
                    print(f"\n📈 实体提取进度:")
                    print(f"  [{bar}] {percent:.1f}%")
                    print(f"  {progress}/{total} chunks")
                    
                    # 速度计算
                    if prev_progress > 0 and progress > prev_progress:
                        speed = progress - prev_progress  # 30秒内的进度
                        eta_seconds = (total - progress) / speed * 30 if speed > 0 else 0
                        eta_min = int(eta_seconds // 60)
                        eta_sec = int(eta_seconds % 60)
                        print(f"\n⚡ 速度: {speed} chunks/30s")
                        print(f"⏱️  预计剩余时间: {eta_min}分{eta_sec}秒")
                    
                    prev_progress = progress
                    
                    # 输出统计
                    print(f"\n📦 已生成数据:")
                    print(f"  - 实体数量: {stats.get('entities', 0):,}")
                    print(f"  - 关系数量: {stats.get('relationships', 0):,}")
                    
                    # 错误信息
                    if result.get("errors"):
                        print(f"\n⚠️  最近错误:")
                        for err in result["errors"]:
                            print(f"  - {err[:80]}")
                    
                    # 完成检测
                    if progress >= total and total > 0:
                        print("\n" + "=" * 60)
                        print("🎉 实体提取已完成！")
                        print("=" * 60)
                        break
            
            print("\n" + "-" * 60)
            print("按 Ctrl+C 退出监控...")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")

if __name__ == "__main__":
    main()
