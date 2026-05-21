#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过滤知识图谱中的低质量节点
移除图表编号、页码、纯数字等无意义节点
"""

import networkx as nx
import re
import sys
from pathlib import Path

def is_valid_node(node_id):
    """
    判断节点是否有效
    返回 True 表示有效节点，False 表示应该过滤掉
    """
    if not node_id or not isinstance(node_id, str):
        return False
    
    # 解码 HTML 实体（如果存在）
    try:
        import html
        node_id = html.unescape(node_id)
    except:
        pass
    
    node_id_clean = node_id.strip()
    
    # 过滤掉空字符串
    if not node_id_clean:
        return False
    
    # 过滤掉图表编号
    if re.match(r'^图\d+[-.]?\d*$', node_id_clean):
        return False
    if re.match(r'^FIGURE\s*\d+[-.]?\d*$', node_id_clean, re.IGNORECASE):
        return False
    if re.match(r'^图\s*\d+[-.]?\d*', node_id_clean):
        return False
    if re.match(r'^TABLE\s*\d+[-.]?\d*$', node_id_clean, re.IGNORECASE):
        return False
    
    # 过滤掉纯数字（可能是页码或编号）
    if node_id_clean.isdigit():
        return False
    
    # 过滤掉简单的编号模式（如 "5.3", "1.2.1"）
    if re.match(r'^\d+\.\d+(\.\d+)*$', node_id_clean):
        return False
    
    # 过滤掉时间相关节点（年份、年代等）
    if re.match(r'^\d{4}年$', node_id_clean):  # 如 "1953年"
        return False
    if re.match(r'^\d+世纪\d+年代$', node_id_clean):  # 如 "20世纪90年代"
        return False
    if re.match(r'^\d+年代$', node_id_clean):  # 如 "90年代"
        return False
    
    # 过滤掉常见的人物、国家、组织名称（如果被错误提取）
    # 注意：这里只过滤明显的人名和国家名，避免误杀材料名称
    common_names = ['WHINFIELD', 'DICKSON', '美国', '日本', '英国', '中国', '我国']
    if node_id_clean in common_names:
        return False
    
    # 过滤掉公司名称（组织）
    if '公司' in node_id_clean and len(node_id_clean) < 20:  # 如"日本钟纺公司"、"旭化成公司"、"拜耳公司"
        return False
    
    # 过滤掉单位节点（包含单位符号的节点）
    if re.search(r'CN·DTEX|G·ML|DTEX|ML|%|H$', node_id_clean):  # 如"CN·DTEX-1"、"G·ML-1"、"14H"、"5%伸长"、"吸水率达30%"
        return False
    if re.match(r'^\d+%', node_id_clean):  # 如"30%"、"5%"
        return False
    
    # 过滤掉过短的节点（可能是噪声）
    if len(node_id_clean) < 2:
        return False
    
    # 过滤掉只包含特殊字符的节点（至少需要包含字母或中文）
    if not re.search(r'[a-zA-Z\u4e00-\u9fff]', node_id_clean):
        return False
    
    # 过滤掉只包含单个字符或符号的节点
    if len(node_id_clean) == 1 and not node_id_clean.isalnum():
        return False
    
    # 过滤掉超长节点（可能是思维链内容或错误解析）
    # 正常实体名称通常不会超过100个字符
    if len(node_id_clean) > 100:
        return False
    
    # 过滤掉包含思维链关键词的节点（模型思考过程被错误解析为实体）
    thinking_keywords = [
        r'我现在需要',
        r'仔细检查',
        r'用户提供',
        r'首先.*其次',
        r'接下来',
        r'检查.*遗漏',
        r'重新.*分析',
        r'确保.*遗漏',
        r'实体部分',
        r'关系部分',
        r'可能遗漏',
        r'需要添加',
        r'补充.*关系',
        r'重新整理',
        r'RELATIONSHIP',
        r'ENTITY',
        r'思考过程',
        r'思维链',
    ]
    
    for pattern in thinking_keywords:
        if re.search(pattern, node_id_clean, re.IGNORECASE):
            return False
    
    # 过滤掉包含明显思考过程结构的节点（如 "1. **材料**"、"2. **工艺**" 等）
    if re.search(r'\d+\.\s*\*\*', node_id_clean):
        return False
    
    # 过滤掉包含多个连续问号的节点（思考过程特征）
    if '？？' in node_id_clean or node_id_clean.count('?') > 2:
        return False
    
    # 过滤掉包含明显思考语句的节点（如 "是否"、"可能"、"需要" 等频繁出现）
    thinking_phrases = ['是否应', '可能', '需要', '应该', '可以', '但是', '不过', '根据', '例如']
    thinking_count = sum(1 for phrase in thinking_phrases if phrase in node_id_clean)
    if thinking_count >= 3:  # 如果包含3个或以上思考短语，很可能是思维链内容
        return False
    
    return True

def filter_graph(input_file, output_file=None, verbose=True):
    """
    过滤知识图谱文件
    
    Args:
        input_file: 输入的 GraphML 文件路径
        output_file: 输出的 GraphML 文件路径，如果为 None 则自动生成
        verbose: 是否显示详细信息
    
    Returns:
        输出文件路径，如果失败则返回 None
    """
    if not Path(input_file).exists():
        if verbose:
            print(f"错误: 输入文件不存在: {input_file}", file=sys.stderr)
        return None
    
    try:
        if verbose:
            print(f"正在读取图谱文件: {input_file}")
        G = nx.read_graphml(input_file)
        
        original_nodes = len(G.nodes())
        original_edges = len(G.edges())
        
        if verbose:
            print(f"原始节点数: {original_nodes}")
            print(f"原始边数: {original_edges}")
        
        # 过滤节点
        valid_nodes = [n for n in G.nodes() if is_valid_node(n)]
        invalid_nodes = set(G.nodes()) - set(valid_nodes)
        
        if invalid_nodes and verbose:
            print(f"\n发现 {len(invalid_nodes)} 个无效节点，将被过滤:")
            for node in sorted(list(invalid_nodes))[:20]:  # 只显示前20个
                print(f"  - {node}")
            if len(invalid_nodes) > 20:
                print(f"  ... 还有 {len(invalid_nodes) - 20} 个节点")
        
        # 创建过滤后的子图
        G_filtered = G.subgraph(valid_nodes).copy()
        
        filtered_nodes = len(G_filtered.nodes())
        filtered_edges = len(G_filtered.edges())
        
        if verbose:
            print(f"\n过滤后节点数: {filtered_nodes}")
            print(f"过滤后边数: {filtered_edges}")
        
        # 确定输出文件路径
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"
        else:
            output_file = Path(output_file)
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存过滤后的图谱
        if verbose:
            print(f"\n正在保存过滤后的图谱: {output_file}")
        nx.write_graphml(G_filtered, str(output_file))
        
        if verbose:
            print("[OK] 过滤完成")
            print(f"  移除了 {len(invalid_nodes)} 个无效节点")
            print(f"  保留了 {filtered_nodes} 个有效节点")
            print(f"  移除了 {original_edges - filtered_edges} 条边")
        
        return str(output_file)
    
    except Exception as e:
        if verbose:
            print(f"错误: 处理图谱文件时发生异常: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        return None

if __name__ == "__main__":
    import sys
    
    # 默认处理 graphrag/output/graph.graphml
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "graphrag/output/graph.graphml"
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = None
    
    filter_graph(input_file, output_file)

