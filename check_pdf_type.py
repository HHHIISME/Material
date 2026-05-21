#!/usr/bin/env python3
"""
检查 PDF 文件是否为扫描版
并估算 token 成本
"""

import fitz  # PyMuPDF
from pathlib import Path
import random

data_dir = r"D:\桌面\agent\Material\data"
pdf_files = list(Path(data_dir).rglob("*.pdf"))

print("=" * 80)
print("🔍 PDF 文件类型检查")
print("=" * 80)
print(f"\n总 PDF 文件数: {len(pdf_files)}")

# 随机抽样检查
sample_size = 20
sample_files = random.sample(pdf_files, min(sample_size, len(pdf_files)))

print(f"\n正在随机检查 {len(sample_files)} 个样本文件...\n")

scanned_count = 0
text_count = 0
error_count = 0

for pdf_path in sample_files:
    doc = None
    try:
        doc = fitz.open(pdf_path)
        total_text = ""
        total_images = 0
        num_pages = len(doc)
        
        # 检查前 5 页
        for page_num in range(min(5, num_pages)):
            page = doc[page_num]
            total_text += page.get_text()
            total_images += len(page.get_images())
        
        avg_text_per_page = len(total_text) / min(5, num_pages)
        is_scanned = len(total_text) < 100  # 如果前5页文本少于100字符，认为是扫描版
        
        if is_scanned:
            scanned_count += 1
            status = "⚠️ 扫描版"
        else:
            text_count += 1
            status = "✅ 文本版"
        
        print(f"{pdf_path.name[:50]:<52} 页数:{num_pages:<4} 文本:{len(total_text):<6} 图片:{total_images:<3} {status}")
        
    except Exception as e:
        error_count += 1
        print(f"{pdf_path.name[:50]:<52} ❌ 错误: {str(e)[:30]}")
    
    finally:
        if doc is not None:
            doc.close()

print("\n" + "=" * 80)
print("📊 检查结果统计")
print("=" * 80)
print(f"扫描版 PDF: {scanned_count} ({scanned_count/len(sample_files)*100:.1f}%)")
print(f"文本版 PDF: {text_count} ({text_count/len(sample_files)*100:.1f}%)")
print(f"读取错误: {error_count} ({error_count/len(sample_files)*100:.1f}%)")

# 估算成本
print("\n" + "=" * 80)
print("💰 Token 成本估算")
print("=" * 80)

if scanned_count > text_count:
    print("\n⚠️  检测到大部分 PDF 为扫描版，需要 OCR 处理\n")
    
    # 统计总页数
    print("正在统计所有 PDF 的总页数（这可能需要几分钟）...")
    total_pages = 0
    checked = 0
    
    for pdf_path in pdf_files:
        doc = None
        try:
            doc = fitz.open(pdf_path)
            total_pages += len(doc)
            checked += 1
            
            if checked % 100 == 0:
                print(f"  已检查 {checked}/{len(pdf_files)} 个文件...")
            
        except:
            pass
        finally:
            if doc is not None:
                doc.close()
    
    print(f"\n总页数: {total_pages:,}")
    
    # OCR 成本
    print("\n【方案A：OCR + GraphRAG】")
    print("  步骤1: OCR 识别")
    ocr_cost_per_page = 0.015  # 百度 OCR 标准版价格
    ocr_total_cost = total_pages * ocr_cost_per_page
    print(f"    - OCR 成本: {total_pages:,} 页 × ¥{ocr_cost_per_page} = ¥{ocr_total_cost:,.2f}")
    
    print("\n  步骤2: GraphRAG 处理")
    # 假设每页平均 500 字
    estimated_total_chars = total_pages * 500
    estimated_total_tokens = estimated_total_chars / 4  # 英文为主
    
    print(f"    - 预估字符数: {estimated_total_chars:,}")
    print(f"    - 预估 tokens: {estimated_total_tokens:,.0f}")
    
    # GraphRAG 成本
    chunk_size = 1200
    num_chunks = int(estimated_total_tokens / chunk_size) + 1
    
    # GLM-4-flash 价格
    input_price_per_1k = 0.0001  # 元/千token
    output_price_per_1k = 0.0001
    
    extraction_input_cost = (num_chunks * (2000 + chunk_size) / 1000) * input_price_per_1k
    extraction_output_cost = (num_chunks * 500 / 1000) * output_price_per_1k
    graphrag_cost = extraction_input_cost + extraction_output_cost
    
    print(f"    - GraphRAG 成本: ¥{graphrag_cost:,.2f}")
    
    print(f"\n  💵 总成本: ¥{ocr_total_cost + graphrag_cost:,.2f}")
    print(f"     （OCR: ¥{ocr_total_cost:,.2f} + GraphRAG: ¥{graphrag_cost:,.2f}）")
    
    print("\n【方案B：使用文本版 PDF 或纯文本】（推荐）")
    print("  如果能获取文本版 PDF 或纯文本数据：")
    print(f"    - 预估 tokens: {estimated_total_tokens:,.0f}")
    print(f"    - 成本: ¥{graphrag_cost:,.2f}")
    print(f"  💰 可节省: ¥{ocr_total_cost:,.2f}（OCR 成本）")
    
    print("\n【方案C：PaddleOCR 本地处理】（最省钱）")
    print("  使用 PaddleOCR 本地识别（免费），只需 GraphRAG 成本：")
    print(f"    - 总成本: ¥{graphrag_cost:,.2f}")
    print(f"  💰 可节省: ¥{ocr_total_cost:,.2f}（OCR 成本）")
    print("  ⚠️  注意：需要安装 PaddleOCR 并有足够的计算资源")

elif text_count > 0:
    print("\n✅ 检测到部分文本版 PDF\n")
    
    # 读取文本并计算 tokens
    print("正在读取文本内容估算 tokens...")
    total_text_length = 0
    
    for pdf_path in sample_files[:10]:
        doc = None
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            total_text_length += len(text)
        except:
            pass
        finally:
            if doc is not None:
                doc.close()
    
    avg_text_length = total_text_length / min(10, text_count) if text_count > 0 else 0
    estimated_total_tokens = (avg_text_length * len(pdf_files)) / 4
    
    print(f"  平均每本字符数: {avg_text_length:,.0f}")
    print(f"  预估总 tokens: {estimated_total_tokens:,.0f}")
    
    # GraphRAG 成本
    chunk_size = 1200
    num_chunks = int(estimated_total_tokens / chunk_size) + 1
    
    input_price_per_1k = 0.0001
    output_price_per_1k = 0.0001
    
    extraction_input_cost = (num_chunks * (2000 + chunk_size) / 1000) * input_price_per_1k
    extraction_output_cost = (num_chunks * 500 / 1000) * output_price_per_1k
    total_cost = extraction_input_cost + extraction_output_cost
    
    print(f"\n💰 GraphRAG 总成本: ¥{total_cost:,.2f}")

else:
    print("\n❌ 无法读取任何 PDF 文件，请检查文件格式")

print("\n" + "=" * 80)
print("⚠️  重要提示")
print("=" * 80)
print("1. 以上为粗略估算，实际成本可能因文献质量而异")
print("2. 建议先用小样本（10-50篇）测试")
print("3. 如果是扫描版，建议使用 PaddleOCR 本地处理（免费）")
print("4. GraphRAG 支持增量处理，可以分批导入数据")
