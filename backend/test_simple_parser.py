"""
测试简化版PDF解析器
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.pdf_parser import pdf_parser


def test_simple_parser():
    """测试简化版PDF解析器"""
    pdf_path = r"D:\桌面\攻防实践\GEO.pdf"
    
    print(f"\n{'='*80}")
    print(f"测试简化版PDF解析器: {pdf_path}")
    print(f"{'='*80}\n")
    
    # 解析PDF
    result = pdf_parser.parse_pdf(file_path=pdf_path)
    
    if not result.success:
        print(f"❌ 解析失败: {result.error}")
        return
    
    # 输出总体信息
    print(f"✅ 解析成功!")
    print(f"   - 文件名: {result.filename}")
    print(f"   - 总页数: {result.total_pages}")
    print(f"   - 解析耗时: {result.parse_time}")
    
    # 测试图注提取
    full_text = "\n".join([page.text for page in result.pages])
    captions = pdf_parser.extract_captions_from_text(full_text)
    
    print(f"\n📝 提取到的图注 ({len(captions)} 个):")
    for i, caption in enumerate(captions[:10], 1):  # 只显示前10个
        print(f"   {i}. {caption}")
    
    # 测试页面渲染
    print(f"\n🖼️  测试页面渲染...")
    page_img = pdf_parser.get_page_image(file_path=pdf_path, page_num=0)
    if page_img:
        print(f"   ✅ 成功渲染第1页，大小: {len(page_img)} 字节")
    else:
        print(f"   ❌ 页面渲染失败")
    
    print(f"\n✅ 测试完成!\n")


if __name__ == "__main__":
    test_simple_parser()
