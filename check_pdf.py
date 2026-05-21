#!/usr/bin/env python3
"""
检查 PDF 文件是否有文本层
"""

import fitz  # PyMuPDF
from pathlib import Path

data_dir = r"D:\桌面\agent\Material\data"
pdf_files = list(Path(data_dir).rglob("*.pdf"))[:5]

print("检查前 5 个 PDF 文件：\n")

for pdf_path in pdf_files:
    print(f"📄 {pdf_path.name}")
    try:
        doc = fitz.open(pdf_path)
        
        # 检查页数
        print(f"   页数: {len(doc)}")
        
        # 检查第一页
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()
            print(f"   文本长度: {len(text)} 字符")
            
            # 检查是否有图片
            images = page.get_images()
            print(f"   图片数量: {len(images)}")
            
            # 如果文本长度为 0，但有图片，说明是扫描版
            if len(text) == 0 and len(images) > 0:
                print(f"   ⚠️  可能是扫描版 PDF")
            
            # 显示前 100 个字符
            if len(text) > 0:
                print(f"   文本预览: {text[:100]}...")
        
        doc.close()
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print()
