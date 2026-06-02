"""
知识图谱 API 响应模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class EntityResponse(BaseModel):
    """实体响应"""
    id: int
    name: str
    type: str
    description: Optional[str] = None
    source_doc: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class EntityListResponse(BaseModel):
    """实体列表响应"""
    total: int
    items: list[EntityResponse]
    page: int
    page_size: int


class EntityTypeStat(BaseModel):
    """实体类型统计"""
    type: str
    count: int


class EntityStatsResponse(BaseModel):
    """实体统计"""
    total: int
    by_type: list[EntityTypeStat]


class RelationshipResponse(BaseModel):
    """关系响应"""
    id: int
    source_id: int
    target_id: int
    source_name: Optional[str] = None
    target_name: Optional[str] = None
    relation_type: str
    description: Optional[str] = None
    weight: Optional[float] = None
    source_doc: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelationshipListResponse(BaseModel):
    """关系列表响应"""
    total: int
    items: list[RelationshipResponse]
    page: int
    page_size: int


class GraphNode(BaseModel):
    """图谱节点（用于可视化）"""
    id: int
    name: str
    type: str
    degree: int = Field(0, description="节点度数（关联的关系数）")


class GraphLink(BaseModel):
    """图谱边"""
    source: int
    target: int
    relation_type: str
    weight: Optional[float] = 1.0


class SubgraphResponse(BaseModel):
    """子图响应（用于图谱可视化）"""
    center_entity: EntityResponse
    nodes: list[GraphNode]
    links: list[GraphLink]
    depth: int
    total_nodes: int
    total_links: int
