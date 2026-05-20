"""
智谱API测试脚本
用于验证智谱AI API连接和功能
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 加载.env文件
env_path = backend_dir.parent / ".env"
load_dotenv(env_path)

from app.services.zhipu_service import ZhipuService


def test_chat():
    """测试对话功能"""
    print("=" * 50)
    print("测试智谱AI对话功能...")
    print("=" * 50)
    
    service = ZhipuService()
    
    # 测试简单对话
    result = service.chat(
        message="你好，请介绍一下材料科学的基本概念。",
        model="glm-4-flash"
    )
    
    if result["success"]:
        print("\n✅ 对话测试成功!")
        print(f"模型: {result['model']}")
        print(f"Token使用: {result['usage']}")
        print(f"\n回复内容:\n{result['content']}")
    else:
        print(f"\n❌ 对话测试失败: {result['error']}")


def test_embedding():
    """测试嵌入功能"""
    print("\n" + "=" * 50)
    print("测试智谱AI嵌入功能...")
    print("=" * 50)
    
    service = ZhipuService()
    
    # 测试文本嵌入
    test_text = "材料科学是研究材料的结构、性能、加工工艺和应用之间关系的学科。"
    
    result = service.embed(text=test_text, model="embedding-3")
    
    if result["success"]:
        print("\n✅ 嵌入测试成功!")
        print(f"模型: {result['model']}")
        print(f"向量维度: {result['dimension']}")
        print(f"向量前10个值: {result['embedding'][:10]}")
    else:
        print(f"\n❌ 嵌入测试失败: {result['error']}")


def test_batch_embedding():
    """测试批量嵌入功能"""
    print("\n" + "=" * 50)
    print("测试智谱AI批量嵌入功能...")
    print("=" * 50)
    
    service = ZhipuService()
    
    # 测试批量嵌入
    test_texts = [
        "金属材料具有优良的导电性和延展性。",
        "陶瓷材料具有高硬度和耐高温特性。",
        "高分子材料具有轻质和易加工的特点。"
    ]
    
    result = service.batch_embed(texts=test_texts, model="embedding-3")
    
    if result["success"]:
        print("\n✅ 批量嵌入测试成功!")
        print(f"模型: {result['model']}")
        print(f"向量数量: {result['count']}")
        print(f"向量维度: {result['dimension']}")
    else:
        print(f"\n❌ 批量嵌入测试失败: {result['error']}")


if __name__ == "__main__":
    print("\n🚀 开始测试智谱AI API...\n")
    
    try:
        test_chat()
        test_embedding()
        test_batch_embedding()
        print("\n" + "=" * 50)
        print("✅ 所有测试完成!")
        print("=" * 50 + "\n")
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
