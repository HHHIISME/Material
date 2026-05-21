#!/usr/bin/env python3
"""
Token 成本计算工具
用于估算 GraphRAG 处理文献的 token 成本
"""

import os
import re
from pathlib import Path

# 智谱 AI 价格（2026年5月）
GLM4_FLASH_INPUT_PRICE = 0.0001  # 元/千token
GLM4_FLASH_OUTPUT_PRICE = 0.0001  # 元/千token
EMBEDDING_PRICE = 0.0005  # 元/千token

# GraphRAG 提示词长度（估算）
GRAPHRAG_PROMPT_TOKENS = 2000  # 提取实体的提示词约 2000 tokens

def count_tokens(text: str) -> int:
    """
    粗略估算 token 数量
    英文: 1 token ≈ 4 字符
    中文: 1 token ≈ 1.5 字符
    """
    # 区分中英文
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(text) - chinese_chars
    
    # 计算 tokens
    chinese_tokens = chinese_chars / 1.5
    english_tokens = english_chars / 4
    
    return int(chinese_tokens + english_tokens)

def estimate_graphrag_cost(text_length: int, num_docs: int) -> dict:
    """
    估算 GraphRAG 处理成本
    
    GraphRAG 流程：
    1. 文本分块（chunk_size=1200 tokens，overlap=100）
    2. 每个块调用 LLM 提取实体和关系
    3. 实体和关系向量化
    4. 社区检测（不需要 LLM）
    5. 生成社区报告（需要 LLM）
    """
    # 1. 文本分块
    chunk_size = 1200
    overlap = 100
    effective_chunk_size = chunk_size - overlap
    
    # 估算总 token 数
    total_tokens = text_length / 4  # 假设主要是英文
    num_chunks = int(total_tokens / effective_chunk_size) + 1
    
    # 2. 实体提取成本
    # 每个块：输入 = 提示词 + 文本块，输出 ≈ 500 tokens
    extraction_input = num_chunks * (GRAPHRAG_PROMPT_TOKENS + chunk_size)
    extraction_output = num_chunks * 500
    
    # 3. 向量化成本（实体描述）
    # 平均每块提取 10 个实体，每个实体描述约 50 tokens
    embedding_tokens = num_chunks * 10 * 50
    
    # 4. 社区报告成本（估算）
    # 假设生成 20 个社区，每个社区报告约 1000 tokens
    community_reports_input = 20 * (1000 + 500)  # 输入
    community_reports_output = 20 * 1000  # 输出
    
    # 总计
    total_input = extraction_input + community_reports_input
    total_output = extraction_output + community_reports_output
    total_embedding = embedding_tokens
    
    # 计算成本
    input_cost = (total_input / 1000) * GLM4_FLASH_INPUT_PRICE
    output_cost = (total_output / 1000) * GLM4_FLASH_OUTPUT_PRICE
    embedding_cost = (total_embedding / 1000) * EMBEDDING_PRICE
    total_cost = input_cost + output_cost + embedding_cost
    
    return {
        "文档数量": num_docs,
        "文本长度（字符）": text_length,
        "分块数量": num_chunks,
        "总输入tokens": total_input,
        "总输出tokens": total_output,
        "向量化tokens": total_embedding,
        "输入成本（元）": round(input_cost, 4),
        "输出成本（元）": round(output_cost, 4),
        "向量化成本（元）": round(embedding_cost, 4),
        "总成本（元）": round(total_cost, 4)
    }

def estimate_from_files(directory: str, num_sample_files: int = 10) -> dict:
    """
    从实际文件估算成本
    """
    # 获取所有 PDF 文件
    pdf_files = list(Path(directory).rglob("*.pdf"))
    
    if len(pdf_files) == 0:
        print(f"❌ 未找到 PDF 文件")
        return None
    
    # 读取样本文件
    sample_files = pdf_files[:num_sample_files]
    
    print(f"\n📖 正在读取 {len(sample_files)} 个样本文件...")
    print(f"   （总共 {len(pdf_files)} 个 PDF 文件）\n")
    
    total_text_length = 0
    
    for pdf_path in sample_files:
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            text_length = len(text)
            total_text_length += text_length
            
            print(f"✅ {pdf_path.name}: {text_length:,} 字符")
            
        except Exception as e:
            print(f"❌ {pdf_path.name}: 读取失败 - {e}")
    
    if total_text_length == 0:
        print("❌ 所有样本文件读取失败")
        return None
    
    # 计算平均值
    avg_text_length = total_text_length / len(sample_files)
    
    # 估算全部文献的成本
    total_docs = len(pdf_files)
    total_text = avg_text_length * total_docs
    
    print(f"\n📊 样本统计：")
    print(f"   样本文件数: {len(sample_files)}")
    print(f"   平均文本长度: {avg_text_length:,.0f} 字符")
    print(f"   总文件数: {total_docs}")
    print(f"   预估总字符数: {total_text:,.0f}")
    
    # 测试规模
    print(f"\n💰 成本估算：")
    
    # 1. 小样本测试（10篇）
    small_sample_cost = estimate_graphrag_cost(avg_text_length * 10, 10)
    print(f"\n   【小样本测试】（10篇文献）")
    for key, value in small_sample_cost.items():
        print(f"      {key}: {value:,}" if isinstance(value, int) else f"      {key}: {value}")
    
    # 2. 中等规模测试（50篇）
    medium_sample_cost = estimate_graphrag_cost(avg_text_length * 50, 50)
    print(f"\n   【中等规模测试】（50篇文献）")
    print(f"      总成本（元）: {medium_sample_cost['总成本（元）']}")
    
    # 3. 全部文献
    full_cost = estimate_graphrag_cost(total_text, total_docs)
    print(f"\n   【全部文献】（{total_docs}篇）")
    print(f"      总成本（元）: {full_cost['总成本（元）']}")
    
    return {
        "样本文件数": len(sample_files),
        "平均文本长度": avg_text_length,
        "总文件数": total_docs,
        "小样本成本": small_sample_cost['总成本（元）'],
        "中等规模成本": medium_sample_cost['总成本（元）'],
        "全部成本": full_cost['总成本（元）']
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    else:
        data_dir = r"D:\桌面\agent\Material\data"
        sample_size = 10
    
    print("=" * 60)
    print("🔍 GraphRAG Token 成本计算工具")
    print("=" * 60)
    
    result = estimate_from_files(data_dir, sample_size)
    
    if result:
        print("\n" + "=" * 60)
        print("✅ 估算完成")
        print("=" * 60)
