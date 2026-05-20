"""
调试PDF图注提取
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.pdf_parser import PDFParser

def debug_captions(pdf_path: str):
    """调试图注提取"""
    import fitz
    
    # 图注匹配正则表达式（更灵活的匹配）
    CAPTION_PATTERNS = [
        r"图[一二三四五六七八九十\d]+[\-‐–—]\d+[^\n]*",  # 图5-1 xxx
        r"图\s*\d+[\.．]\d+[^\n]*",  # 图5.1 xxx
        r"图\s*\d+[^\n]*",  # 图1 xxx
    ]
    
    # 英文图注匹配（需要包含关键词）
    CAPTION_KEYWORDS = ["Figure", "Fig.", "Fig"]
    
    doc = fitz.open(pdf_path)
    
    print(f"\n{'='*80}")
    print(f"调试PDF图注提取: {pdf_path}")
    print(f"{'='*80}\n")
    
    for page_num in range(min(3, len(doc))):  # 只检查前3页
        page = doc[page_num]
        text_dict = page.get_text("dict")
        
        print(f"\n📄 第 {page_num + 1} 页:")
        print(f"   总块数: {len(text_dict['blocks'])}")
        
        # 检查所有文本块
        caption_count = 0
        for block in text_dict["blocks"]:
            if block.get("type") != 0:  # 跳过非文本块
                continue
            
            text = block.get("text", "").strip()
            
            # 检查是否匹配中文图注格式
            is_caption = False
            for pattern in CAPTION_PATTERNS:
                if re.match(pattern, text):
                    is_caption = True
                    break
            
            # 检查是否包含英文图注关键词
            if not is_caption:
                for keyword in CAPTION_KEYWORDS:
                    if keyword in text:
                        # 检查是否包含数字
                        if re.search(r'\d+', text):
                            is_caption = True
                            break
            
            if is_caption:
                caption_count += 1
                print(f"\n   ✅ 找到图注 #{caption_count}:")
                print(f"      文本: {text[:100]}...")
                print(f"      位置: {block['bbox']}")
        
        if caption_count == 0:
            # 显示所有包含"Figure"或"图"的文本块
            print("\n   ⚠️  没有找到标准图注，查找包含关键词的文本:")
            for i, block in enumerate(text_dict["blocks"]):
                if block.get("type") != 0:
                    continue
                text = block.get("text", "").strip()
                if "Figure" in text or "图" in text or "Fig." in text:
                    print(f"\n      块 #{i}: {repr(text[:200])}")
                    print(f"      位置: {block['bbox']}")
        
        # 显示完整文本以供参考
        if caption_count == 0:
            print("\n   📝 完整文本（前500字符）:")
            full_text = page.get_text()
            print(f"      {full_text[:500]}")
    
    doc.close()


if __name__ == "__main__":
    pdf_path = r"D:\桌面\攻防实践\GEO.pdf"
    debug_captions(pdf_path)
