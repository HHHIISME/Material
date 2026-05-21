"""
知识图谱数据迁移脚本
从 GraphRAG 输出的 parquet 文件导入数据到 PostgreSQL
"""
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from tqdm import tqdm

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, init_db
from app.models.knowledge_graph import Entity, Relationship


def migrate_entities(entities_file: str, db: Session) -> dict:
    """
    迁移实体数据
    
    Args:
        entities_file: entities.parquet 文件路径
        db: 数据库会话
    
    Returns:
        映射字典 {原ID: 新ID}
    """
    print("\n📊 开始迁移实体数据...")
    
    # 读取 parquet 文件
    entities_df = pd.read_parquet(entities_file)
    print(f"   找到 {len(entities_df)} 个实体")
    
    # 清空现有数据
    db.query(Relationship).delete()
    db.query(Entity).delete()
    db.commit()
    print("   ✓ 清空现有数据")
    
    # ID映射字典
    id_mapping = {}
    
    # 批量插入
    for idx, row in tqdm(entities_df.iterrows(), total=len(entities_df), desc="导入实体"):
        # 创建实体
        entity = Entity(
            name=row.get('title', '')[:500],  # 限制长度
            type=row.get('type', 'UNKNOWN')[:50],
            description=row.get('description', ''),
            source_doc=row.get('source_doc', '')[:100] if pd.notna(row.get('source_doc')) else None
        )
        db.add(entity)
        db.flush()  # 获取自增ID
        
        # 记录ID映射
        original_id = row.get('id', idx)
        id_mapping[original_id] = entity.id
    
    db.commit()
    print(f"   ✅ 成功导入 {len(entities_df)} 个实体")
    
    return id_mapping


def migrate_relationships(relationships_file: str, id_mapping: dict, db: Session):
    """
    迁移关系数据
    
    Args:
        relationships_file: relationships.parquet 文件路径
        id_mapping: 实体ID映射字典
        db: 数据库会话
    """
    print("\n📊 开始迁移关系数据...")
    
    # 读取 parquet 文件
    relationships_df = pd.read_parquet(relationships_file)
    print(f"   找到 {len(relationships_df)} 个关系")
    
    # 统计
    success_count = 0
    skip_count = 0
    
    # 批量插入
    for idx, row in tqdm(relationships_df.iterrows(), total=len(relationships_df), desc="导入关系"):
        # 获取映射后的ID
        source_id = id_mapping.get(row.get('source'))
        target_id = id_mapping.get(row.get('target'))
        
        # 检查ID是否存在
        if source_id is None or target_id is None:
            skip_count += 1
            continue
        
        # 创建关系
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=row.get('type', 'RELATED_TO')[:200],
            description=row.get('description', ''),
            weight=float(row.get('weight', 1.0)) if pd.notna(row.get('weight')) else 1.0,
            source_doc=row.get('source_doc', '')[:100] if pd.notna(row.get('source_doc')) else None
        )
        db.add(relationship)
        success_count += 1
    
    db.commit()
    print(f"   ✅ 成功导入 {success_count} 个关系")
    if skip_count > 0:
        print(f"   ⚠️  跳过 {skip_count} 个关系（实体不存在）")


def verify_migration(db: Session):
    """验证迁移结果"""
    print("\n📊 验证迁移结果...")
    
    entity_count = db.query(Entity).count()
    relationship_count = db.query(Relationship).count()
    
    print(f"   实体数量: {entity_count}")
    print(f"   关系数量: {relationship_count}")
    
    # 统计实体类型分布
    from sqlalchemy import func
    entity_types = db.query(
        Entity.type,
        func.count(Entity.id).label('count')
    ).group_by(Entity.type).all()
    
    print("\n   实体类型分布:")
    for type_name, count in entity_types:
        print(f"     - {type_name}: {count}")
    
    return entity_count, relationship_count


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 知识图谱数据迁移工具")
    print("=" * 60)
    
    # 数据文件路径
    graphrag_output = Path("D:/桌面/agent/Material/KnowledgeGraph/KnowledgeGraph/graphrag/output")
    entities_file = graphrag_output / "entities.parquet"
    relationships_file = graphrag_output / "relationships.parquet"
    
    # 检查文件是否存在
    if not entities_file.exists():
        print(f"❌ 文件不存在: {entities_file}")
        return
    
    if not relationships_file.exists():
        print(f"❌ 文件不存在: {relationships_file}")
        return
    
    print(f"\n📂 数据文件:")
    print(f"   实体文件: {entities_file}")
    print(f"   关系文件: {relationships_file}")
    
    # 初始化数据库
    print("\n⚙️  初始化数据库...")
    init_db()
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 迁移实体
        id_mapping = migrate_entities(str(entities_file), db)
        
        # 迁移关系
        migrate_relationships(str(relationships_file), id_mapping, db)
        
        # 验证迁移
        entity_count, relationship_count = verify_migration(db)
        
        print("\n" + "=" * 60)
        print("✅ 数据迁移完成！")
        print(f"   实体总数: {entity_count}")
        print(f"   关系总数: {relationship_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
