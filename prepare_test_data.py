#!/usr/bin/env python3
"""
从 data 目录抽取文本版 PDF 并转换为 GraphRAG 输入格式
"""

import fitz  # PyMuPDF
from pathlib import Path
import random
import shutil

def extract_text_from_pdf(pdf_path):
    """从 PDF 提取文本"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text if len(text) > 100 else None
    except Exception as e:
        print(f"  ❌ 提取失败: {e}")
        return None

def main():
    data_dir = r"D:\桌面\agent\Material\data"
    graphrag_input_dir = r"D:\桌面\agent\Material\KnowledgeGraph\KnowledgeGraph\graphrag\input"
    
    print("=" * 80)
    print("📦 准备 GraphRAG 测试数据")
    print("=" * 80)
    
    # 1. 清空 input 目录（保留原有文件备份）
    input_path = Path(graphrag_input_dir)
    if input_path.exists():
        # 备份现有文件
        backup_dir = input_path.parent / "input_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(input_path, backup_dir)
        print(f"\n✅ 已备份原有文件到: {backup_dir}")
        
        # 清空 input 目录
        shutil.rmtree(input_path)
        input_path.mkdir()
        print(f"✅ 已清空 input 目录")
    
    # 2. 获取所有 PDF 文件
    print(f"\n🔍 正在扫描 data 目录...")
    all_pdfs = list(Path(data_dir).rglob("*.pdf"))
    print(f"   找到 {len(all_pdfs)} 个 PDF 文件")
    
    # 3. 随机抽样
    sample_size = 20
    sample_pdfs = random.sample(all_pdfs, min(sample_size, len(all_pdfs)))
    print(f"\n📝 随机抽取 {len(sample_pdfs)} 个文件进行测试\n")
    
    # 4. 提取文本并保存
    success_count = 0
    total_chars = 0
    
    for i, pdf_path in enumerate(sample_pdfs, 1):
        print(f"[{i}/{len(sample_pdfs)}] 处理: {pdf_path.name[:60]}")
        
        # 提取文本
        text = extract_text_from_pdf(pdf_path)
        
        if text:
            # 保存为 .txt 文件
            output_file = input_path / f"doc_{i:03d}.txt"
            
            # 添加文件名作为标题
            content = f"# {pdf_path.stem}\n\n{text}"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            success_count += 1
            total_chars += len(text)
            print(f"  ✅ 提取成功: {len(text):,} 字符")
        else:
            print(f"  ⚠️  跳过（文本过少或提取失败）")
    
    # 5. 统计结果
    print("\n" + "=" * 80)
    print("📊 数据准备完成")
    print("=" * 80)
    print(f"  成功提取: {success_count}/{len(sample_pdfs)} 个文件")
    print(f"  总字符数: {total_chars:,}")
    print(f"  平均字符数: {total_chars//success_count:,}" if success_count > 0 else "")
    print(f"\n  输出目录: {input_path}")
    print(f"  文件列表:")
    
    # 列出生成的文件
    for f in sorted(input_path.glob("*.txt")):
        print(f"    - {f.name}")
    
    # 6. 估算成本
    print("\n" + "=" * 80)
    print("💰 预估 GraphRAG 成本")
    print("=" * 80)
    
    # Token 估算
    estimated_tokens = total_chars / 3  # 混合中英文
    
    # GraphRAG 成本计算
    chunk_size = 1200
    num_chunks = int(estimated_tokens / chunk_size) + 1
    
    # GLM-4-flash 价格
    input_price_per_1k = 0.0001
    output_price_per_1k = 0.0001
    embedding_price_per_1k = 0.0005
    
    # 实体提取
    extraction_input_cost = (num_chunks * (2000 + chunk_size) / 1000) * input_price_per_1k
    extraction_output_cost = (num_chunks * 500 / 1000) * output_price_per_1k
    embedding_cost = (num_chunks * 10 * 50 / 1000) * embedding_price_per_1k
    
    total_cost = extraction_input_cost + extraction_output_cost + embedding_cost
    
    print(f"  预估 tokens: {estimated_tokens:,.0f}")
    print(f"  预估分块数: {num_chunks:,}")
    print(f"  预估成本: ¥{total_cost:.4f}")
    
    print("\n✅ 准备就绪！现在可以运行 GraphRAG 了")
    print(f"\n运行命令:")
    print(f"  cd {input_path.parent}")
    print(f"  python -m graphrag index --root . --verbose")

if __name__ == "__main__":
    main()
