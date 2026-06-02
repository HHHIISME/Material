"""
关系查询 API
提供关系的列表、按实体查询、按关系类型过滤、关系类型分布
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge_graph import Entity, Relationship
from app.api.v1.schemas.kg import (
    RelationshipResponse,
    RelationshipListResponse,
)

router = APIRouter(prefix="/relationships", tags=["知识图谱-关系"])


@router.get("", response_model=RelationshipListResponse)
async def list_relationships(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    relation_type: str | None = Query(None, description="按关系类型过滤"),
    source_doc: str | None = Query(None, description="按来源文档过滤"),
    db: Session = Depends(get_db),
):
    """
    列出关系，支持分页、类型/来源过滤
    """
    query = db.query(Relationship)
    if relation_type:
        query = query.filter(Relationship.relation_type == relation_type)
    if source_doc:
        query = query.filter(Relationship.source_doc == source_doc)

    total = query.count()
    items = (
        query.order_by(Relationship.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return RelationshipListResponse(
        total=total,
        items=[RelationshipResponse(**r.to_dict()) for r in items],
        page=page,
        page_size=page_size,
    )


@router.get("/by-entity/{entity_id}", response_model=RelationshipListResponse)
async def get_relationships_by_entity(
    entity_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    direction: str = Query("both", pattern="^(out|in|both)$", description="出度/入度/双向"),
    db: Session = Depends(get_db),
):
    """
    查询与某实体相关的所有关系

    - direction=out：实体作为 source 的关系
    - direction=in：实体作为 target 的关系
    - direction=both：双向
    """
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"实体 {entity_id} 不存在")

    query = db.query(Relationship)
    if direction == "out":
        query = query.filter(Relationship.source_id == entity_id)
    elif direction == "in":
        query = query.filter(Relationship.target_id == entity_id)
    else:
        query = query.filter(
            (Relationship.source_id == entity_id)
            | (Relationship.target_id == entity_id)
        )

    total = query.count()
    items = (
        query.order_by(Relationship.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return RelationshipListResponse(
        total=total,
        items=[RelationshipResponse(**r.to_dict()) for r in items],
        page=page,
        page_size=page_size,
    )


@router.get("/types")
async def get_relationship_types(db: Session = Depends(get_db)):
    """
    关系类型分布
    """
    rows = (
        db.query(
            Relationship.relation_type,
            func.count(Relationship.id).label("count"),
        )
        .group_by(Relationship.relation_type)
        .order_by(func.count(Relationship.id).desc())
        .all()
    )
    return {
        "total": sum(r.count for r in rows),
        "by_type": [{"relation_type": r.relation_type, "count": r.count} for r in rows],
    }


@router.get("/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(relationship_id: int, db: Session = Depends(get_db)):
    """
    按 ID 查询关系
    """
    rel = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail=f"关系 {relationship_id} 不存在")
    return RelationshipResponse(**rel.to_dict())
