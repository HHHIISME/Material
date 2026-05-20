"""
测试PDF解析器的图片位置、图注提取和引用识别功能
"""
import sys
import os
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pdf_parser import PDFParser, PDFParseResult


def test_pdf_parsing(pdf_path: str):
    """
    测试PDF解析
    
    Args:
        pdf_path: PDF文件路径
    """
    print(f"\n{'='*80}")
    print(f"测试PDF解析: {pdf_path}")
    print(f"{'='*80}\n")
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    # 创建解析器
    parser = PDFParser(extract_images=True, extract_tables=True)
    
    # 解析PDF
    print("📖 开始解析PDF...")
    result = parser.parse_pdf(file_path=pdf_path)
    
    if not result.success:
        print(f"❌ 解析失败: {result.error}")
        return
    
    # 输出总体信息
    print(f"\n✅ 解析成功!")
    print(f"   - 文件名: {result.filename}")
    print(f"   - 总页数: {result.total_pages}")
    print(f"   - 总图片数: {result.total_images}")
    print(f"   - 有图注的图片数: {result.images_with_caption}")
    print(f"   - 图片引用数: {result.total_references}")
    print(f"   - 解析耗时: {result.parse_time}")
    
    # 输出每一页的详细信息
    print(f"\n{'='*80}")
    print("页面详情:")
    print(f"{'='*80}\n")
    
    for page in result.pages:
        print(f"📄 第 {page.page_number} 页 ({page.width:.0f} x {page.height:.0f})")
        
        # 显示图片信息
        if page.images:
            print(f"   🖼️  图片 ({len(page.images)} 个):")
            for img in page.images:
                print(f"      - ID: {img.image_id}")
                print(f"        尺寸: {img.width} x {img.height}")
                if img.bbox:
                    print(f"        位置: ({img.bbox[0]:.1f}, {img.bbox[1]:.1f}, {img.bbox[2]:.1f}, {img.bbox[3]:.1f})")
                if img.caption:
                    print(f"        图注: {img.caption}")
                print()
        
        # 显示图片引用
        if page.image_references:
            print(f"   🔗 图片引用 ({len(page.image_references)} 个):")
            for ref in page.image_references:
                print(f"      - {ref.ref_text} → {ref.image_id}")
            print()
        
        # 显示表格信息
        if page.tables:
            print(f"   📊 表格 ({len(page.tables)} 个)")
            print()
        
        # 显示前200字符的文本
        text_preview = page.text[:200].replace('\n', ' ')
        print(f"   📝 文本预览: {text_preview}...")
        print()
    
    # 保存详细结果到JSON
    output_file = pdf_path.replace('.pdf', '_parse_result.json')
    print(f"\n💾 保存详细结果到: {output_file}")
    
    # 转换为可序列化的字典
    result_dict = result.model_dump()
    
    # 处理bytes类型（无法JSON序列化）
    for page in result_dict['pages']:
        for img in page['images']:
            if img.get('image_bytes'):
                img['image_bytes'] = f"<{len(img['image_bytes'])} bytes>"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 测试完成!\n")


if __name__ == "__main__":
    # 使用指定的PDF文件
    pdf_path = r"D:\桌面\攻防实践\GEO.pdf"
    
    test_pdf_parsing(pdf_path)
