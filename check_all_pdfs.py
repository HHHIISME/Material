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
sample_size = 30
sample_files = random.sample(pdf_files, min(sample_size, len(pdf_files)))

print(f"\n正在随机检查 {len(sample_files)} 个样本文件...\n")

scanned_count = 0
text_count = 0
error_count = 0

sample_details = []

for pdf_path in sample_files:
    try:
        doc = fitz.open(pdf_path)
        total_text = ""
        total_images = 0
        
        # 检查前 5 页
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            total_text += page.get_text()
            total_images += len(page.get_images())
        
        doc.close()
        
        avg_text_per_page = len(total_text) / min(5, len(doc))
        is_scanned = len(total_text) < 100  # 如果前5页文本少于100字符，认为是扫描版
        
        if is_scanned:
            scanned_count += 1
            status = "⚠️ 扫描版"
        else:
            text_count += 1
            status = "✅ 文本版"
        
        sample_details.append({
            "文件": pdf_path.name[:40],
            "页数": len(doc),
            "前5页文本": len(total_text),
            "图片数": total_images,
            "状态": status
        })
        
    except Exception as e:
        error_count += 1
        sample_details.append({
            "文件": pdf_path.name[:40],
            "页数": "错误",
            "前5页文本": "错误",
            "图片数": "错误",
            "状态": f"❌ {str(e)[:20]}"
        })

# 显示结果
print(f"\n{'文件名':<42} {'页数':<8} {'前5页文本':<12} {'图片数':<8} {'状态'}")
print("-" * 80)
for detail in sample_details[:15]:
    print(f"{detail['文件']:<42} {str(detail['页数']):<8} {str(detail['前5页文本']):<12} {str(detail['图片数']):<8} {detail['状态']}")

if len(sample_details) > 15:
    print(f"... 还有 {len(sample_details) - 15} 个样本")

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

# 假设所有 PDF 都是扫描版
if scanned_count > text_count:
    print("\n⚠️  检测到大部分 PDF 为扫描版，需要 OCR 处理\n")
    
    # 统计总页数
    print("正在统计所有 PDF 的总页数...")
    total_pages = 0
    for pdf_path in pdf_files[:100]:  # 只检查前100个，避免太慢
        try:
            doc = fitz.open(pdf_path)
            total_pages += len(doc)
            doc.close()
        except:
            pass
    
    avg_pages = total_pages / 100
    estimated_total_pages = int(avg_pages * len(pdf_files))
    
    print(f"   样本页数（前100个PDF）: {total_pages}")
    print(f"   平均每本页数: {avg_pages:.1f}")
    print(f"   预估总页数: {estimated_total_pages:,}")
    
    # OCR 成本
    print("\n【方案A：OCR + GraphRAG】")
    print("  步骤1: OCR 识别")
    ocr_cost_per_page = 0.015  # 百度 OCR 标准版价格
    ocr_total_cost = estimated_total_pages * ocr_cost_per_page
    print(f"    - OCR 成本: {estimated_total_pages:,} 页 × ¥{ocr_cost_per_page} = ¥{ocr_total_cost:,.2f}")
    
    print("\n  步骤2: GraphRAG 处理")
    # 假设每页平均 500 字
    estimated_total_chars = estimated_total_pages * 500
    estimated_total_tokens = estimated_total_chars / 4  # 英文为主
    
    print(f"    - 预估字符数: {estimated_total_chars:,}")
    print(f"    - 预估 tokens: {estimated_total_tokens:,.0f}")
    
    # GraphRAG 成本（参考之前的计算）
    chunk_size = 1200
    num_chunks = int(estimated_total_tokens / chunk_size) + 1
    
    # GLM-4-flash 价格
    input_price = 0.0001 / 1000  # 元/token
    output_price = 0.0001 / 1000
    
    extraction_input = num_chunks * (2000 + chunk_size) * input_price
    extraction_output = num_chunks * 500 * output_price
    graphrag_cost = extraction_input + extraction_output
    
    print(f"    - GraphRAG 成本: ¥{graphrag_cost:,.2f}")
    
    print(f"\n  💵 总成本: ¥{ocr_total_cost + graphrag_cost:,.2f}")
    print(f"     （OCR: ¥{ocr_total_cost:,.2f} + GraphRAG: ¥{graphrag_cost:,.2f}）")
    
    print("\n【方案B：使用文本版 PDF 或纯文本】（推荐）")
    print("  如果能获取文本版 PDF 或纯文本数据：")
    print(f"    - 预估 tokens: {estimated_total_tokens:,.0f}")
    print(f"    - 成本: ¥{graphrag_cost:,.2f}")
    print(f"  💰 可节省: ¥{ocr_total_cost:,.2f}（OCR 成本）")

else:
    print("\n✅ 大部分 PDF 为文本版，可以直接处理\n")
    # 读取文本并计算 tokens
    # （这里需要实际读取文本）
    print("需要进一步读取文本内容来准确估算...")

print("\n" + "=" * 80)
print("⚠️  重要提示")
print("=" * 80)
print("1. 以上为粗略估算，实际成本可能因文献质量而异")
print("2. OCR 识别率会影响 GraphRAG 提取效果")
print("3. 建议先用小样本（10-50篇）测试")
print("4. 可以考虑使用更便宜的 OCR 方案（PaddleOCR 本地部署）")
