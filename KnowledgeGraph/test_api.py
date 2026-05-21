import requests
import json

api_key = '598318f7b13040d5a598cb0bf7a4c400.p44I8nAUNRmDGRW3'
url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

# 测试1: 基本实体提取
test_prompt = """-Goal-
Identify all entities from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. Format each entity as ("entity"<|>entity_name<|>entity_type<|>entity_description)

2. Identify all pairs of related entities. Format each relationship as ("relationship"<|>source_entity<|>target_entity<|>relationship_description<|>relationship_strength)

3. Return output in English as a single list. Use ## as the list delimiter.

4. When finished, output COMPLETE

######################
Text:
Polyimide is a high-performance polymer with excellent thermal stability. It is widely used in aerospace applications. The polyimide aerogel exhibits low thermal conductivity of 0.023 W/mK and can withstand temperatures up to 590 degrees Celsius. Carbon fiber reinforcement improves the mechanical strength of polyimide composites.
######################
Output:"""

response = requests.post(
    url,
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json={
        'model': 'glm-4-flash',
        'messages': [{'role': 'user', 'content': test_prompt}],
        'temperature': 0
    }
)

result = response.json()
print('=== Test 1: Entity Extraction ===')
print('Status:', response.status_code)
if 'choices' in result:
    content = result['choices'][0]['message']['content']
    print('Response:')
    print(content)
else:
    print('Error:', json.dumps(result, ensure_ascii=False, indent=2))

# 测试2: 模拟 GraphRAG 实际 prompt 格式
print('\n\n=== Test 2: GraphRAG-style Prompt ===')

graphrag_prompt = """-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [MATERIAL, PROCESS, STRUCTURE, PROPERTY, TECHNOLOGY, EQUIPMENT, APPLICATION]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity
- target_entity: name of the target entity
- relationship_description: explanation
- relationship_strength: a numeric score indicating strength
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)

3. Return output in English as a single list. Use **{record_delimiter}** as the list delimiter.

4. When finished, output {completion_delimiter}

Text:
Polyimide aerogel exhibits low thermal conductivity of 0.023 W/mK. Carbon fiber reinforcement improves mechanical strength.
"""

# 替换占位符
graphrag_prompt = graphrag_prompt.replace('{tuple_delimiter}', '<|>')
graphrag_prompt = graphrag_prompt.replace('{record_delimiter}', '##')
graphrag_prompt = graphrag_prompt.replace('{completion_delimiter}', 'COMPLETE')

response2 = requests.post(
    url,
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json={
        'model': 'glm-4-flash',
        'messages': [{'role': 'user', 'content': graphrag_prompt}],
        'temperature': 0
    }
)

result2 = response2.json()
print('Status:', response2.status_code)
if 'choices' in result2:
    content2 = result2['choices'][0]['message']['content']
    print('Response:')
    print(content2[:2000])
else:
    print('Error:', json.dumps(result2, ensure_ascii=False, indent=2))
