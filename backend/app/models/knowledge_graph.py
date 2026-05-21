"""
知识图谱数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Entity(Base):
    """实体表"""
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True, comment="实体名称")
    type = Column(String(50), nullable=False, index=True, comment="实体类型")
    description = Column(Text, comment="实体描述")
    source_doc = Column(String(100), comment="来源文档")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    relationships_as_source = relationship("Relationship", foreign_keys="Relationship.source_id", back_populates="source_entity")
    relationships_as_target = relationship("Relationship", foreign_keys="Relationship.target_id", back_populates="target_entity")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "source_doc": self.source_doc,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Relationship(Base):
    """关系表"""
    __tablename__ = "relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True, comment="源实体ID")
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True, comment="目标实体ID")
    relation_type = Column(String(200), nullable=False, comment="关系类型")
    description = Column(Text, comment="关系描述")
    weight = Column(Float, default=1.0, comment="关系权重")
    source_doc = Column(String(100), comment="来源文档")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    source_entity = relationship("Entity", foreign_keys=[source_id], back_populates="relationships_as_source")
    target_entity = relationship("Entity", foreign_keys=[target_id], back_populates="relationships_as_target")
    
    def to_dict(self):
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_name": self.source_entity.name if self.source_entity else None,
            "target_name": self.target_entity.name if self.target_entity else None,
            "relation_type": self.relation_type,
            "description": self.description,
            "weight": self.weight,
            "source_doc": self.source_doc,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
