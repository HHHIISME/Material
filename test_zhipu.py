#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试智谱 AI API 响应格式"""

import os
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key=os.environ.get("ZHIPU_API_KEY", "598318f7b13040d5a598cb0bf7a4c400.p44I8nAUNRmDGRW3"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# 测试提示词（简化版）
test_prompt = """-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.
 
-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [MATERIAL, APPLICATION, PROPERTY]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"<|><entity_name><|><entity_type><|><entity_description>)
 
2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
 Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><relationship_strength>)
 
3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **##** as the list delimiter.
 
4. When finished, output <|COMPLETE|>

Text:
Polyimide is a high-performance polymer material known for its excellent thermal stability and mechanical properties. It is widely used in aerospace applications for thermal insulation.
"""

# 测试文本
test_text = "Polyimide is a high-performance polymer material known for its excellent thermal stability and mechanical properties. It is widely used in aerospace applications for thermal insulation."

# 构建完整提示
full_prompt = test_prompt.replace("{entity_types}", "MATERIAL,APPLICATION,PROPERTY")
full_prompt = full_prompt.replace("Text:\n", f"Text:\n{test_text}")

print("=" * 80)
print("Testing Zhipu AI API...")
print("=" * 80)

try:
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.0,
    )
    
    print("\n" + "=" * 80)
    print("Response:")
    print("=" * 80)
    print(response.choices[0].message.content)
    print("\n" + "=" * 80)
    print("Tokens used:", response.usage.total_tokens if response.usage else "N/A")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
