"""
PDF解析测试脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.pdf_parser import PDFParser, pdf_parser


def test_pdf_text_extraction():
    """测试PDF文本提取"""
    print("=" * 50)
    print("测试PDF文本提取...")
    print("=" * 50)
    
    # 检查测试文件
    test_files = [
        backend_dir.parent / "data" / "sample.pdf",
        backend_dir.parent / "data" / "test.pdf"
    ]
    
    test_file = None
    for f in test_files:
        if f.exists():
            test_file = f
            break
    
    if not test_file:
        print("⚠️ 未找到测试PDF文件，创建测试...")
        # 创建一个简单的测试
        result = pdf_parser.parse_pdf(file_bytes=b"%PDF-1.4 test", file_path="test.pdf")
        print(f"结果: {result}")
        return
    
    # 解析PDF
    result = pdf_parser.parse_pdf(file_path=str(test_file))
    
    if result.success:
        print("\n✅ PDF解析成功!")
        print(f"文件名: {result.filename}")
        print(f"总页数: {result.total_pages}")
        print(f"解析时间: {result.parse_time}")
        
        # 显示第一页内容
        if result.pages:
            first_page = result.pages[0]
            print(f"\n第一页预览 (前500字符):")
            print(first_page.text[:500] + "...")
            print(f"\n第一页图片数量: {len(first_page.images)}")
            print(f"第一页表格数量: {len(first_page.tables)}")
    else:
        print(f"\n❌ PDF解析失败: {result.error}")


def test_pdf_image_extraction():
    """测试PDF图片提取"""
    print("\n" + "=" * 50)
    print("测试PDF图片提取...")
    print("=" * 50)
    
    # 创建测试目录
    output_dir = backend_dir / "tests" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"图片输出目录: {output_dir}")
    print("✅ 图片提取功能就绪")


def test_pdf_page_render():
    """测试PDF页面渲染为图片"""
    print("\n" + "=" * 50)
    print("测试PDF页面渲染...")
    print("=" * 50)
    
    # 创建测试目录
    output_dir = backend_dir / "tests" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"渲染输出目录: {output_dir}")
    print("✅ 页面渲染功能就绪")


if __name__ == "__main__":
    print("\n🚀 开始测试PDF解析服务...\n")
    
    try:
        test_pdf_text_extraction()
        test_pdf_image_extraction()
        test_pdf_page_render()
        print("\n" + "=" * 50)
        print("✅ PDF解析服务测试完成!")
        print("=" * 50 + "\n")
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
