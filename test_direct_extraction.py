"""
直接测试 GraphRAG 实体提取
"""
import os
import sys
import asyncio

# 添加项目路径
sys.path.insert(0, r'D:\桌面\agent\Material\backend\venv\Lib\site-packages')

from graphrag.llm import OpenAIExtensions
from graphrag.prompt_tuning.prompt import create_entity_extraction_prompt

async def test_extraction():
    # 配置
    api_key = "598318f7b13040d5a598cb0bf7a4c400.p44I8nAUNRmDGRW3"
    api_base = "https://open.bigmodel.cn/api/paas/v4/"
    model = "glm-4-flash"
    
    # 测试文本
    text = "聚酰亚胺是一种高性能聚合物材料,具有优异的热稳定性和机械性能。"
    entity_types = ["material", "process", "structure", "property", "technology", "equipment", "application"]
    
    # 创建提示
    prompt = create_entity_extraction_prompt(text, entity_types)
    
    print("=" * 80)
    print("Prompt:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # 调用 API
    llm = OpenAIExtensions(
        api_key=api_key,
        api_base=api_base,
        model=model
    )
    
    print("\nCalling Zhipu AI API...")
    response = await llm.agenerate(prompt)
    
    print("=" * 80)
    print("Response:")
    print("=" * 80)
    print(response)
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_extraction())
