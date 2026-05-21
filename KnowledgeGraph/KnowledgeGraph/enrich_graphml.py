#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 GraphML 文件添加实体描述和关系描述
从 entities.parquet 和 relationships.parquet 读取信息，并添加到 GraphML 中
"""

import pandas as pd
import xml.etree.ElementTree as ET
import html
import sys
from pathlib import Path


def decode_html_entities(text):
    """解码 HTML 实体"""
    if not text:
        return text
    try:
        return html.unescape(str(text))
    except:
        return str(text)


def encode_html_entities(text):
    """编码 HTML 实体（如果需要）"""
    if not text:
        return text
    text = str(text)
    # 先解码，然后重新编码（避免双重编码）
    text = decode_html_entities(text)
    # GraphML 需要编码特殊字符
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')


def clean_description(desc):
    """清理描述文本，移除 LLM 思考过程和重复内容"""
    if not desc:
        return desc
    
    desc = str(desc)
    
    import re
    
    # 先解码 HTML 实体
    desc = html.unescape(desc)
    
    # 移除明显的思考过程标记（更彻底的清理）
    thinking_patterns = [
        # 中文思考过程
        r'好的，我现在需要.*?(?=&lt;|</think>|思考过程|&lt;/think&gt;|实际内容|描述：|定义：|是|指|属于)',
        r'首先，.*?接下来，.*?最后，',
        r'我需要.*?确保.*?',
        r'检查.*?遗漏',
        r'重新.*?分析',
        r'仔细检查.*?',
        r'按照.*?要求.*?',
        r'用户指出.*?',
        r'用户要求.*?',
        r'用户提供.*?',
        r'用户的目标.*?',
        r'完全理解.*?',
        r'确保.*?正确',
        r'可能.*?需要',
        r'应该.*?属于',
        r'可能属于',
        r'需要看.*?',
        r'例如，.*?',
        r'另外，.*?',
        r'此外，.*?',
        r'不过.*?',
        r'但是.*?',
        r'所以.*?',
        r'因此.*?',
        r'从文本文档中.*?',
        r'构建知识图谱.*?',
        r'实体类型包括.*?',
        r'关系规则.*?',
        r'关系强度.*?',
        r'原文本.*?',
        r'只显示到.*?',
        r'的实际数据.*?',
        r'但原文本.*?',
        r'可能：\(&quot;.*?',
        r'看是否合适.*?',
        r'仿生技术基础\).*?',
        r'仿生技术原理\).*?',
        r'&amp;lt;\|.*?',
        r'&lt;\|.*?',
        # 英文思考过程
        r'Okay, let.*?(?=&lt;|</think>|&lt;/think&gt;|The |实际内容|描述：)',
        r'Looking at.*?',
        r'So, the task.*?',
        r'I should.*?',
        r'Maybe add.*?',
        r'Since the user.*?',
        r'Keep it under.*?',
        r'Make sure.*?',
        r'I need to.*?',
        r'First,.*?',
        r'Then,.*?',
        r'Finally,.*?',
        r'Also,.*?',
        r'Additionally,.*?',
        r'However,.*?',
        r'Therefore,.*?',
        # XML 标签
        r'&lt;think&gt;.*?&lt;/think&gt;',
        r'&lt;redacted_reasoning&gt;.*?&lt;/redacted_reasoning&gt;',
        r'<think>.*?</think>',
    ]
    
    for pattern in thinking_patterns:
        desc = re.sub(pattern, '', desc, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除以思考过程开头的描述（如果整个描述都是思考过程）
    thinking_starters = [
        r'^(好的，我现在需要|Okay, let|Looking at|So, the task|I should|Maybe add|Since the user|首先，|接下来，|最后，|我需要|检查|重新|仔细检查|按照|用户指出|用户要求|用户提供|用户的目标|完全理解|确保|可能|应该|需要看|例如|另外|此外|不过|但是|所以|因此|从文本文档|构建知识图谱|实体类型|关系规则|原文本|只显示到|的实际数据|但原文本)',
        r'^(材料好的，我现在需要|性能好的，我现在需要|工艺好的，我现在需要)',
    ]
    
    for starter in thinking_starters:
        if re.match(starter, desc, re.IGNORECASE):
            # 尝试提取实际内容（通常在思考过程之后）
            match = re.search(r'(&lt;/think&gt;|</think>|思考过程结束|实际内容：|描述：|定义：|是|指|属于)(.*)', desc, re.DOTALL | re.IGNORECASE)
            if match:
                desc = match.group(2)
            else:
                # 如果找不到实际内容，返回空
                return ''
    
    # 移除重复的句子（检测连续重复的句子）
    sentences = re.split(r'[。！？\.\!\?]\s*', desc)
    unique_sentences = []
    seen = set()
    for sent in sentences:
        sent = sent.strip()
        if sent and len(sent) > 5:  # 只处理有意义的句子
            # 归一化句子（移除标点、空格）用于比较
            normalized = re.sub(r'[^\w]', '', sent.lower())
            if normalized not in seen and len(normalized) > 3:
                seen.add(normalized)
                unique_sentences.append(sent)
    
    desc = '。'.join(unique_sentences)
    if desc and not desc.endswith(('。', '!', '?', '.', '!', '?')):
        desc += '。'
    
    # 移除多余的空行和空格
    desc = re.sub(r'\s+', ' ', desc).strip()
    
    # 如果描述太短（可能是被清理掉了），返回空
    if len(desc) < 10:
        return ''
    
    # 如果描述仍然包含大量思考过程关键词，返回空
    thinking_keywords = [
        '好的，我现在需要', 'Okay, let', 'Looking at', 'So, the task', 'I should', 
        'Maybe add', 'Since the user', 'Keep it under', 'Make sure', '首先，',
        '接下来，', '最后，', '我需要', '检查', '重新', '仔细检查', '按照',
        '用户指出', '用户要求', '用户提供', '完全理解', '确保', '可能', '应该',
        '从文本文档', '构建知识图谱', '实体类型', '关系规则', '原文本', '只显示到',
        '的实际数据', '但原文本', '但似乎被截断', '材料指出', '他们的要求', '是全面识别',
        '有明确的指向性', '分为强、中、弱', '是第5章的',
        '从文本文档', '构建知识图谱', '实体类型', '关系规则', '原文本', '只显示到',
        '的实际数据', '但原文本', '可能：', '看是否合适', '仿生技术基础', '仿生技术原理'
    ]
    thinking_count = sum(1 for keyword in thinking_keywords if keyword.lower() in desc.lower())
    if thinking_count >= 2:  # 如果包含2个或更多思考关键词，可能是思考过程
        return ''
    
    # 如果描述主要是思考过程（超过50%是思考关键词），返回空
    desc_lower = desc.lower()
    thinking_chars = sum(len(kw) for kw in thinking_keywords if kw.lower() in desc_lower)
    if len(desc) > 0 and thinking_chars / len(desc) > 0.3:  # 超过30%是思考关键词
        return ''
    
    return desc


def load_entities(entities_file):
    """加载实体数据"""
    df = pd.read_parquet(entities_file)
    # 创建以 title 为键的字典（title 是节点的显示名称）
    entities = {}
    for _, row in df.iterrows():
        title = str(row['title']) if pd.notna(row['title']) else ''
        entities[title] = {
            'type': str(row['type']) if pd.notna(row['type']) else '',
            'description': str(row['description']) if pd.notna(row['description']) else '',
            'frequency': int(row['frequency']) if pd.notna(row['frequency']) else 0,
            'degree': int(row['degree']) if pd.notna(row['degree']) else 0,
        }
    return entities


def load_relationships(relationships_file):
    """加载关系数据"""
    df = pd.read_parquet(relationships_file)
    # 创建以 (source, target) 为键的字典
    relationships = {}
    for _, row in df.iterrows():
        source = str(row['source']) if pd.notna(row['source']) else ''
        target = str(row['target']) if pd.notna(row['target']) else ''
        # 使用元组作为键，同时考虑两个方向（因为是无向图）
        key1 = (source, target)
        key2 = (target, source)
        rel_info = {
            'description': str(row['description']) if pd.notna(row['description']) else '',
            'weight': float(row['weight']) if pd.notna(row['weight']) else 0.0,
        }
        relationships[key1] = rel_info
        relationships[key2] = rel_info  # 无向图，两个方向都存储
    return relationships


def enrich_graphml(graphml_file, entities_file, relationships_file, output_file):
    """为 GraphML 文件添加实体描述和关系描述"""
    
    print(f"正在读取实体数据: {entities_file}")
    entities = load_entities(entities_file)
    print(f"  加载了 {len(entities)} 个实体")
    
    print(f"正在读取关系数据: {relationships_file}")
    relationships = load_relationships(relationships_file)
    print(f"  加载了 {len(relationships) // 2} 个关系（无向图）")
    
    print(f"正在解析 GraphML 文件: {graphml_file}")
    tree = ET.parse(graphml_file)
    root = tree.getroot()
    
    # 移除命名空间前缀（如果存在），统一处理
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}')[1]
    
    # 查找或创建属性定义
    graph = root.find('.//graph')
    
    # 检查是否已有 description 和 type 的 key 定义（移除命名空间后直接查找）
    keys = root.findall('.//key')
    
    key_ids = {}
    for key in keys:
        key_id = key.get('id')
        attr_name = key.get('attr.name')
        if attr_name:
            key_ids[attr_name] = key_id
    
    # 添加节点属性定义（如果不存在）
    if 'description' not in key_ids:
        new_key = ET.SubElement(root, 'key')
        new_key.set('id', f'd{len(keys)}')
        new_key.set('for', 'node')
        new_key.set('attr.name', 'description')
        new_key.set('attr.type', 'string')
        key_ids['description'] = new_key.get('id')
        print("  添加了节点 description 属性定义")
    
    if 'type' not in key_ids:
        new_key = ET.SubElement(root, 'key')
        new_key.set('id', f'd{len(keys) + 1}')
        new_key.set('for', 'node')
        new_key.set('attr.name', 'type')
        new_key.set('attr.type', 'string')
        key_ids['type'] = new_key.get('id')
        print("  添加了节点 type 属性定义")
    
    if 'frequency' not in key_ids:
        new_key = ET.SubElement(root, 'key')
        new_key.set('id', f'd{len(keys) + 2}')
        new_key.set('for', 'node')
        new_key.set('attr.name', 'frequency')
        new_key.set('attr.type', 'int')
        key_ids['frequency'] = new_key.get('id')
        print("  添加了节点 frequency 属性定义")
    
    # 添加边属性定义（如果不存在）
    if 'edge_description' not in key_ids:
        new_key = ET.SubElement(root, 'key')
        new_key.set('id', f'd{len(keys) + 3}')
        new_key.set('for', 'edge')
        new_key.set('attr.name', 'description')
        new_key.set('attr.type', 'string')
        key_ids['edge_description'] = new_key.get('id')
        print("  添加了边 description 属性定义")
    
    # 处理节点（已移除命名空间，直接查找）
    nodes = root.findall('.//node')
    enriched_nodes = 0
    for node in nodes:
        node_id = node.get('id')
        if not node_id:
            continue
        
        # 解码 HTML 实体以匹配实体名称
        decoded_id = decode_html_entities(node_id)
        
        # 查找对应的实体信息
        entity_info = entities.get(decoded_id)
        if not entity_info:
            # 尝试直接匹配（可能已经是解码后的）
            entity_info = entities.get(node_id)
        
        if entity_info:
            # 清理并添加 description
            cleaned_desc = clean_description(entity_info['description'])
            if cleaned_desc:
                desc_elem = ET.SubElement(node, 'data')
                desc_elem.set('key', key_ids['description'])
                desc_elem.text = encode_html_entities(cleaned_desc)
            
            # 添加 type（清理并验证类型值）
            type_value = str(entity_info['type']).strip()
            # 只保留有效的实体类型
            valid_types = ['MATERIAL', 'PROCESS', 'PROPERTY', 'STRUCTURE', 'TECHNOLOGY', 'EQUIPMENT', 'APPLICATION']
            
            # 如果类型值包含思考过程关键词或太长，视为无效
            thinking_in_type = any(kw in type_value for kw in ['好的，我现在需要', 'Okay, let', '用户指出', '用户要求', '用户提供', '检查', '需要', '可能', '应该', '首先', '接下来', '最后', '从文本文档', '构建知识图谱', '实体类型', '关系规则'])
            # 如果类型值太长（超过20个字符），可能是思考过程
            if len(type_value) > 20:
                thinking_in_type = True
            
            if type_value not in valid_types or thinking_in_type:
                # 首先检查是否包含有效类型作为子串（优先提取，按优先级顺序）
                found_type = None
                # 按优先级顺序检查（PROPERTY 优先，因为很多性能名称不包含"性能"）
                priority_order = ['PROPERTY', 'MATERIAL', 'PROCESS', 'STRUCTURE', 'TECHNOLOGY', 'EQUIPMENT', 'APPLICATION']
                for vt in priority_order:
                    if vt in type_value.upper():
                        found_type = vt
                        break
                
                # 如果没找到，尝试从节点名称推断（简单规则）
                if not found_type:
                    node_name_lower = decoded_id.lower()  # 使用解码后的ID
                    # 性能相关关键词（优先级较高，因为很多性能名称不包含"性能"）
                    if any(kw in node_name_lower for kw in ['性能', '强度', '模量', '密度', '弹性', '硬度', '显色', '消色', '变色', '透气', '吸湿', '阻燃', '导电', '吸附', '复合', '功能化', '耐', '抗', '可逆性', '回复率', '伸长率', '稳定性', '热性', '水性', '缩水', '膨胀', '变硬']):
                        found_type = 'PROPERTY'
                    elif any(kw in node_name_lower for kw in ['纤维', '材料', '聚合物', '溶剂', '化学', '颜料', '蛋白', '聚酯', '聚酰胺', '聚氨酯', '聚丙烯', '聚乙烯']):
                        found_type = 'MATERIAL'
                    elif any(kw in node_name_lower for kw in ['工艺', '方法', '处理', '制备', '加工', '纺丝', '聚合', '氧化', '碳化', '石墨化', '炭化', '深加工']):
                        found_type = 'PROCESS'
                    elif any(kw in node_name_lower for kw in ['结构', '排列', '形态', '组织', '键', '分子结构', '微晶', '多孔', '结晶度', '共聚物']):
                        found_type = 'STRUCTURE'
                    elif any(kw in node_name_lower for kw in ['技术', '原理', '理论', '改性技术', '气相沉积', '引发体系']):
                        found_type = 'TECHNOLOGY'
                    elif any(kw in node_name_lower for kw in ['设备', '仪器', '装置', '机器', '炉', '箱', '器', '机', '混合器', '挤出机', '喷头', '贮槽', '料仓']):
                        found_type = 'EQUIPMENT'
                    elif any(kw in node_name_lower for kw in ['应用', '用途', '领域', '工程', '工业', '部门', '服装', '衣', '服', '制品', '织物']):
                        found_type = 'APPLICATION'
                
                type_value = found_type if found_type else ''
            type_elem = ET.SubElement(node, 'data')
            type_elem.set('key', key_ids['type'])
            type_elem.text = encode_html_entities(type_value)
            
            # 添加 frequency
            freq_elem = ET.SubElement(node, 'data')
            freq_elem.set('key', key_ids['frequency'])
            freq_elem.text = str(entity_info['frequency'])
            
            enriched_nodes += 1
    
    print(f"  为 {enriched_nodes}/{len(nodes)} 个节点添加了描述信息")
    
    # 处理边（已移除命名空间，直接查找）
    edges = root.findall('.//edge')
    enriched_edges = 0
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if not source or not target:
            continue
        
        # 解码 HTML 实体
        decoded_source = decode_html_entities(source)
        decoded_target = decode_html_entities(target)
        
        # 查找对应的关系信息
        rel_key = (decoded_source, decoded_target)
        rel_info = relationships.get(rel_key)
        if not rel_info:
            # 尝试直接匹配
            rel_key = (source, target)
            rel_info = relationships.get(rel_key)
        
        if rel_info and rel_info['description']:
            # 清理并添加 description
            cleaned_desc = clean_description(rel_info['description'])
            if cleaned_desc:
                desc_elem = ET.SubElement(edge, 'data')
                desc_elem.set('key', key_ids['edge_description'])
                desc_elem.text = encode_html_entities(cleaned_desc)
            
            enriched_edges += 1
    
    print(f"  为 {enriched_edges}/{len(edges)} 条边添加了描述信息")
    
    # 保存更新后的 GraphML（确保 key 定义在 graph 之前，不使用命名空间前缀）
    print(f"正在保存增强后的 GraphML: {output_file}")
    
    # 重新组织 XML 结构：确保所有 key 在 graph 之前
    # 先收集所有 key 元素
    all_keys = root.findall('.//key')
    
    # 移除所有现有的 key（稍后重新插入到正确位置）
    for key in all_keys:
        root.remove(key)
    
    # 在 graph 之前插入所有 key（按顺序：d0, d1, d2, d3, d4...）
    graph_elem = root.find('.//graph')
    if graph_elem is not None:
        # 找到 graph 的父元素和位置
        parent = graph_elem.getparent() if hasattr(graph_elem, 'getparent') else root
        graph_index = list(parent).index(graph_elem) if graph_elem in list(parent) else 0
        
        # 按 key ID 排序（d0, d1, d2...）
        sorted_keys = sorted(all_keys, key=lambda k: k.get('id', ''))
        
        # 在 graph 之前插入所有 key
        for i, key in enumerate(sorted_keys):
            parent.insert(graph_index + i, key)
    
    # 写入文件（不使用命名空间前缀）
    ET.register_namespace('', 'http://graphml.graphdrawing.org/xmlns')
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    # 后处理：确保格式正确（移除可能的命名空间前缀，确保 xmlns 属性存在）
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除命名空间前缀（如果存在）
    content = content.replace('ns0:graphml', 'graphml')
    content = content.replace('ns0:key', 'key')
    content = content.replace('ns0:graph', 'graph')
    content = content.replace('ns0:node', 'node')
    content = content.replace('ns0:edge', 'edge')
    content = content.replace('ns0:data', 'data')
    if 'xmlns:ns0=' in content:
        content = content.replace('xmlns:ns0=', 'xmlns=')
    
    # 确保 graphml 标签有 xmlns 属性
    if '<graphml' in content and 'xmlns=' not in content.split('<graphml')[1].split('>')[0]:
        content = content.replace('<graphml', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"', 1)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] 完成")


def main():
    if len(sys.argv) < 2:
        print("用法: python3 enrich_graphml.py <graphml_file> [output_file]")
        print("  如果未指定 output_file，将在原文件名后添加 '_enriched'")
        sys.exit(1)
    
    graphml_file = Path(sys.argv[1])
    if not graphml_file.exists():
        print(f"错误: 找不到文件 {graphml_file}")
        sys.exit(1)
    
    # 确定输出文件
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = graphml_file.parent / f"{graphml_file.stem}_enriched{graphml_file.suffix}"
    
    # 确定 entities 和 relationships 文件位置
    output_dir = graphml_file.parent
    entities_file = output_dir / "entities.parquet"
    relationships_file = output_dir / "relationships.parquet"
    
    if not entities_file.exists():
        print(f"错误: 找不到实体文件 {entities_file}")
        sys.exit(1)
    
    if not relationships_file.exists():
        print(f"错误: 找不到关系文件 {relationships_file}")
        sys.exit(1)
    
    enrich_graphml(graphml_file, entities_file, relationships_file, output_file)


if __name__ == "__main__":
    main()

