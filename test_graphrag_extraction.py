"""
测试 GraphRAG 实体提取完整流程
"""
import os
import json
from openai import OpenAI

def test_graphrag_extraction():
    # 配置
    api_key = "598318f7b13040d5a598cb0bf7a4c400.p44I8nAUNRmDGRW3"
    api_base = "https://open.bigmodel.cn/api/paas/v4/"
    model = "glm-4-flash"
    
    # 读取提示模板
    prompt_file = r"D:\桌面\agent\Material\KnowledgeGraph\KnowledgeGraph\graphrag\prompts\extract_graph.txt"
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # 替换实体类型
    entity_types = ["material", "process", "structure", "property", "technology", "equipment", "application"]
    prompt = prompt_template.replace("{entity_types}", ",".join(entity_types))
    
    # 添加测试文本
    test_text = "聚酰亚胺是一种高性能聚合物材料,具有优异的热稳定性和机械性能。它广泛应用于航空航天领域。"
    
    # 构建完整提示（GraphRAG 会在提示后面添加文本）
    full_prompt = prompt + "\n######################\nText:\n" + test_text + "\n######################\nOutput:"
    
    print("=" * 80)
    print("Full Prompt:")
    print("=" * 80)
    print(full_prompt)
    print("=" * 80)
    
    # 调用 API
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    print("\nCalling Zhipu AI API...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.0
    )
    
    result = response.choices[0].message.content
    
    print("=" * 80)
    print("Response:")
    print("=" * 80)
    print(result)
    print("=" * 80)
    
    # 尝试解析响应
    print("\nParsing response...")
    
    # GraphRAG 使用 ## 分割记录
    records = result.split("##")
    
    entities = []
    relationships = []
    
    for record in records:
        record = record.strip()
        if not record:
            continue
        
        # 移除可能的列表标记
        if record.startswith("- "):
            record = record[2:]
        
        # 检查是否是实体
        if record.startswith('("entity"'):
            # 提取实体信息
            try:
                # 移除外层括号
                content = record.strip('()')
                parts = content.split('<|>')
                if len(parts) >= 4:
                    entity_type = parts[0].strip('"')
                    entity_name = parts[1]
                    entity_category = parts[2]
                    entity_description = parts[3]
                    entities.append({
                        "name": entity_name,
                        "type": entity_category,
                        "description": entity_description
                    })
                    print(f"✓ Entity: {entity_name} ({entity_category})")
            except Exception as e:
                print(f"✗ Failed to parse entity: {record[:50]}... - {e}")
        
        # 检查是否是关系
        elif record.startswith('("relationship"'):
            try:
                content = record.strip('()')
                parts = content.split('<|>')
                if len(parts) >= 5:
                    rel_type = parts[0].strip('"')
                    source = parts[1]
                    target = parts[2]
                    description = parts[3]
                    strength = parts[4]
                    relationships.append({
                        "source": source,
                        "target": target,
                        "description": description,
                        "strength": strength
                    })
                    print(f"✓ Relationship: {source} -> {target}")
            except Exception as e:
                print(f"✗ Failed to parse relationship: {record[:50]}... - {e}")
    
    print(f"\nTotal entities found: {len(entities)}")
    print(f"Total relationships found: {len(relationships)}")
    
    if entities:
        print("\n✓ SUCCESS: Entities were extracted!")
    else:
        print("\n✗ FAILURE: No entities were extracted")

if __name__ == "__main__":
    test_graphrag_extraction()
