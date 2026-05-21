#!/usr/bin/env python3
"""
最终成本估算脚本：遍历所有PDF，统计总页数并计算GraphRAG成本
"""

import fitz  # PyMuPDF
from pathlib import Path
import time

def main():
    data_dir = r"D:\桌面\agent\Material\data"
    print("=" * 80)
    print("🔍 启动最终成本估算")
    print("=" * 80)

    # 第一步：遍历所有PDF文件并统计总页数
    print("\n📊 正在遍历所有PDF文件并统计总页数，请稍候...\n")
    
    all_pdfs = list(Path(data_dir).rglob("*.pdf"))
    total_pdfs = len(all_pdfs)
    print(f"找到 PDF 文件总数: {total_pdfs}")

    total_pages = 0
    processed_count = 0
    start_time = time.time()

    for pdf_path in all_pdfs:
        doc = None
        try:
            doc = fitz.open(pdf_path)
            total_pages += len(doc)
            processed_count += 1
            
            # 每处理100个文件，输出一次进度
            if processed_count % 100 == 0:
                elapsed = time.time() - start_time
                print(f"  已处理 {processed_count}/{total_pdfs} 个文件，累计页数: {total_pages:,}，耗时: {elapsed:.1f}秒")
        except Exception as e:
            # 忽略个别文件错误，继续处理
            pass
        finally:
            if doc is not None:
                doc.close()

    elapsed_time = time.time() - start_time
    print(f"\n✅ 统计完成！")
    print(f"   成功处理文件数: {processed_count}/{total_pdfs}")
    print(f"   所有PDF总页数: {total_pages:,} 页")
    print(f"   总耗时: {elapsed_time:.1f}秒")

    # 第二步：基于总页数进行成本计算
    print("\n" + "=" * 80)
    print("💰 Token 成本详细计算")
    print("=" * 80)

    # 基础假设（基于典型学术文献数据）
    # 1. 每页平均字符数（中英文混合，考虑图表空白）：约800字符
    # 2. Token转换比例：中文约1.5字符/token，英文约4字符/token。混合按3字符/token估算。
    avg_chars_per_page = 800
    chars_per_token = 3.0
    
    estimated_total_chars = total_pages * avg_chars_per_page
    estimated_total_tokens = estimated_total_chars / chars_per_token

    print(f"\n【基础估算参数】")
    print(f"  • 总页数: {total_pages:,} 页")
    print(f"  • 每页平均字符数: {avg_chars_per_page}")
    print(f"  • Token转换比例: {chars_per_token} 字符/Token")
    print(f"  ➡️  预估总字符数: {estimated_total_chars:,.0f}")
    print(f"  ➡️  预估总Token数: {estimated_total_tokens:,.0f}")

    # GraphRAG 流程成本计算
    # 流程：文本分块 -> 实体/关系提取 -> 向量化 -> 社区报告生成
    
    # 1. 文本分块
    chunk_size = 1200  # GraphRAG 默认 chunk 大小
    overlap = 100      # 重叠 token 数
    effective_chunk_size = chunk_size - overlap
    num_chunks = int(estimated_total_tokens / effective_chunk_size) + 1
    
    print(f"\n【1. 文本分块】")
    print(f"  • 分块大小: {chunk_size} tokens")
    print(f"  • 重叠大小: {overlap} tokens")
    print(f"  • 预估分块数: {num_chunks:,}")

    # 2. 实体/关系提取成本 (LLM)
    # 输入：Prompt(约2000 tokens) + 文本块(1200 tokens)
    # 输出：提取结果(约500 tokens)
    prompt_tokens = 2000
    output_tokens_per_chunk = 500
    
    extraction_input_tokens = num_chunks * (prompt_tokens + chunk_size)
    extraction_output_tokens = num_chunks * output_tokens_per_chunk
    
    # 3. 向量化成本 (Embedding)
    # 每个块平均提取10个实体，每个实体描述约50 tokens
    entities_per_chunk = 10
    entity_desc_tokens = 50
    embedding_tokens = num_chunks * entities_per_chunk * entity_desc_tokens
    
    # 4. 社区报告生成成本 (LLM)
    # 假设最终生成约 num_chunks/20 个社区，每个社区报告约1500 tokens
    num_communities = int(num_chunks / 20)
    community_report_input_tokens = num_communities * 1500
    community_report_output_tokens = num_communities * 1000
    
    print(f"\n【2. Token 用量明细】")
    print(f"  a) 实体提取输入: {extraction_input_tokens:,} tokens")
    print(f"  b) 实体提取输出: {extraction_output_tokens:,} tokens")
    print(f"  c) 向量化文本:   {embedding_tokens:,} tokens")
    print(f"  d) 社区报告输入: {community_report_input_tokens:,} tokens")
    print(f"  e) 社区报告输出: {community_report_output_tokens:,} tokens")
    
    total_input_tokens = extraction_input_tokens + community_report_input_tokens
    total_output_tokens = extraction_output_tokens + community_report_output_tokens
    
    print(f"\n  总输入Tokens: {total_input_tokens:,}")
    print(f"  总输出Tokens: {total_output_tokens:,}")
    print(f"  总向量化Tokens: {embedding_tokens:,}")

    # 5. 价格计算 (GLM-4-flash)
    # 价格参考：https://open.bigmodel.cn/pricing
    # 输入：0.0001元/千tokens
    # 输出：0.0001元/千tokens
    # Embedding：0.0005元/千tokens
    
    input_price_per_1k = 0.0001  # 元
    output_price_per_1k = 0.0001 # 元
    embedding_price_per_1k = 0.0005 # 元
    
    llm_input_cost = (total_input_tokens / 1000) * input_price_per_1k
    llm_output_cost = (total_output_tokens / 1000) * output_price_per_1k
    embedding_cost = (embedding_tokens / 1000) * embedding_price_per_1k
    
    total_cost = llm_input_cost + llm_output_cost + embedding_cost

    print(f"\n" + "=" * 80)
    print(f"💵 最终成本估算 (基于 GLM-4-flash)")
    print("=" * 80)
    print(f"  • LLM 输入成本: ¥{llm_input_cost:,.2f}")
    print(f"  • LLM 输出成本: ¥{llm_output_cost:,.2f}")
    print(f"  • 向量化成本:   ¥{embedding_cost:,.2f}")
    print("-" * 80)
    print(f"  总计成本:       ¥{total_cost:,.2f} 元人民币")
    print("=" * 80)

    # 提供不同处理规模的建议
    print(f"\n💡 分批处理建议:")
    print(f"  建议分批处理，每批约100个PDF，以便控制成本和观察质量。")
    if total_pdfs > 0:
        cost_per_pdf = total_cost / total_pdfs
        print(f"  平均每个PDF成本: ¥{cost_per_pdf:.4f}")
        print(f"  处理前100个PDF预估成本: ¥{cost_per_pdf * 100:.2f}")
        print(f"  处理前500个PDF预估成本: ¥{cost_per_pdf * 500:.2f}")
        print(f"  处理全部{total_pdfs}个PDF预估成本: ¥{total_cost:,.2f}")

    print(f"\n⚠️  注意：此估算基于文本版PDF假设。")
    print(f"   如果您的PDF包含大量扫描图片，需要额外支付OCR成本（每页约0.015元）。")

if __name__ == "__main__":
    main()
