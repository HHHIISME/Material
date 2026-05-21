#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计 GraphRAG 提取成功和失败的 chunk 数量
通过分析日志文件和输出文件来统计
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def count_nodes_in_graphml(graphml_file):
    """统计 GraphML 文件中的节点数量"""
    if not os.path.exists(graphml_file):
        return 0
    
    try:
        tree = ET.parse(graphml_file)
        root = tree.getroot()
        # GraphML 命名空间
        ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
        nodes = root.findall('.//graphml:node', ns)
        return len(nodes)
    except Exception as e:
        print(f"警告: 无法解析 {graphml_file}: {e}")
        return 0

def count_chunks_from_documents(documents_file):
    """从 documents.parquet 统计总 chunk 数量和成功/失败数量"""
    total_chunks = 0
    successful_chunks = 0
    failed_chunks = 0
    
    # 从 documents.parquet 读取
    try:
        import pandas as pd
        if os.path.exists(documents_file):
            df = pd.read_parquet(documents_file)
            total_chunks = len(df)
            
            # 检查哪些chunk成功提取了实体（通过检查是否有相关的实体提取）
            # GraphRAG 会在 documents 中保存提取结果
            # 如果某个chunk有实体提取，则认为成功
            if 'entities' in df.columns:
                successful_chunks = df['entities'].notna().sum()
                failed_chunks = total_chunks - successful_chunks
            elif 'graph' in df.columns:
                # 有些版本可能使用 'graph' 列
                successful_chunks = df['graph'].notna().sum()
                failed_chunks = total_chunks - successful_chunks
            else:
                # 如果无法确定，使用节点数量估算
                # 假设平均每个成功的chunk产生2个节点
                successful_chunks = total_chunks  # 暂时设为总数，后续会修正
                failed_chunks = 0
                
            return total_chunks, successful_chunks, failed_chunks
    except Exception as e:
        print(f"警告: 无法读取 {documents_file}: {e}")
        pass
    
    return total_chunks, successful_chunks, failed_chunks

def count_failed_from_logs(log_dir):
    """从日志文件中统计失败的chunk数量（通过查找token超限错误）"""
    failed_count = 0
    if not log_dir.exists():
        return failed_count
    
    # 查找所有日志文件
    log_files = list(log_dir.glob('*.log'))
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # 统计 "maximum context length" 错误（token超限）
                failed_count += content.count('maximum context length')
        except Exception as e:
            pass
    
    return failed_count

def analyze_extraction_stats(output_dir):
    """分析提取统计信息"""
    output_dir = Path(output_dir)
    
    # 文件路径
    graph_file = output_dir / 'graph.graphml'
    graph_filtered_file = output_dir / 'graph_filtered.graphml'
    documents_file = output_dir / 'documents.parquet'
    stats_file = output_dir / 'stats.json'
    log_dir = output_dir.parent / 'logs'
    
    print("=" * 60)
    print("GraphRAG 提取统计")
    print("=" * 60)
    print()
    
    # 统计节点数量
    nodes_original = count_nodes_in_graphml(graph_file)
    nodes_filtered = count_nodes_in_graphml(graph_filtered_file)
    
    print(f"📊 节点统计:")
    print(f"  - 原始图谱节点数: {nodes_original}")
    print(f"  - 过滤后节点数: {nodes_filtered}")
    print()
    
    # 统计总 chunk 数量
    total_chunks, successful_chunks_parquet, failed_chunks_parquet = count_chunks_from_documents(documents_file)
    
    # 从日志统计失败数量（token超限错误）
    failed_from_logs = count_failed_from_logs(log_dir)
    
    print(f"📄 Chunk 提取统计:")
    if total_chunks > 0:
        print(f"  - 总 Chunk 数量: {total_chunks}")
        
        # 使用多种方法估算成功/失败数量
        # 方法1: 基于节点数量（假设平均每个成功的chunk产生2个节点）
        if nodes_original > 0:
            estimated_successful_nodes = min(total_chunks, nodes_original // 2)
            estimated_failed_nodes = total_chunks - estimated_successful_nodes
        else:
            estimated_successful_nodes = 0
            estimated_failed_nodes = total_chunks
        
        # 方法2: 基于日志中的错误数量
        if failed_from_logs > 0:
            estimated_failed_logs = min(total_chunks, failed_from_logs)
            estimated_successful_logs = total_chunks - estimated_failed_logs
        else:
            estimated_failed_logs = 0
            estimated_successful_logs = total_chunks
        
        # 使用节点数量估算（更可靠）
        # 假设平均每个成功的chunk产生2个节点
        final_successful = estimated_successful_nodes
        final_failed = estimated_failed_nodes
        method = "节点数量估算"
        
        print(f"  - ✅ 成功提取: {final_successful} ({method})")
        print(f"  - ❌ 失败/跳过: {final_failed} ({method})")
        if total_chunks > 0:
            success_rate = (final_successful / total_chunks) * 100
            print(f"  - 成功率: {success_rate:.1f}%")
        
        # 如果日志中有错误，显示详细信息（但错误可能重复计数，所以只作为参考）
        if failed_from_logs > 0:
            print(f"  - ⚠️  日志中检测到 {failed_from_logs} 个 token 超限错误（可能包含重复）")
            print(f"  - 💡 提示: 实际失败数量可能更少，因为同一错误可能被多次记录")
    else:
        print(f"  - ⚠️  无法确定总 Chunk 数量（文件不存在或无法读取）")
    
    print()
    
    # 读取 stats.json 获取更详细的信息
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                print(f"📈 运行统计 (stats.json):")
                print(f"  - 总运行时间: {stats.get('total_runtime', 0):.1f} 秒")
                print(f"  - 文档数量: {stats.get('num_documents', 0)}")
                if 'workflows' in stats and 'extract_graph' in stats['workflows']:
                    extract_time = stats['workflows']['extract_graph'].get('overall', 0)
                    print(f"  - 图谱提取时间: {extract_time:.1f} 秒")
                print()
        except Exception as e:
            pass
    
    # 检查日志文件（如果存在）
    if log_dir.exists():
        log_files = list(log_dir.glob('*.log'))
        if log_files:
            print(f"📝 日志文件:")
            for log_file in sorted(log_files)[-3:]:  # 只显示最近3个
                size = log_file.stat().st_size / 1024  # KB
                print(f"  - {log_file.name} ({size:.1f} KB)")
            print()
    
    print("=" * 60)
    
    return {
        'nodes_original': nodes_original,
        'nodes_filtered': nodes_filtered,
        'total_chunks': total_chunks,
        'estimated_successful': final_successful if total_chunks > 0 else 0,
        'estimated_failed': final_failed if total_chunks > 0 else 0,
    }

if __name__ == '__main__':
    # 默认输出目录：KnowledgeGraph/graphrag/output
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        script_dir = Path(__file__).resolve().parent.parent
        output_dir = script_dir / 'graphrag' / 'output'
    
    analyze_extraction_stats(output_dir)

