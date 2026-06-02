"""
实体查询 API
提供实体的列表、搜索、按 ID 查询、类型统计功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge_graph import Entity, Relationship
from app.api.v1.schemas.kg import (
    EntityResponse,
    EntityListResponse,
    EntityStatsResponse,
    EntityTypeStat,
)

router = APIRouter(prefix="/entities", tags=["知识图谱-实体"])


@router.get("", response_model=EntityListResponse)
async def list_entities(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    type: str | None = Query(None, description="按实体类型过滤，如 MATERIAL/PROPERTY"),
    source_doc: str | None = Query(None, description="按来源文档过滤"),
    db: Session = Depends(get_db),
):
    """
    列出实体，支持分页、按类型/来源过滤
    """
    query = db.query(Entity)
    if type:
        query = query.filter(Entity.type == type)
    if source_doc:
        query = query.filter(Entity.source_doc == source_doc)

    total = query.count()
    items = (
        query.order_by(Entity.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return EntityListResponse(
        total=total,
        items=[EntityResponse(**e.to_dict()) for e in items],
        page=page,
        page_size=page_size,
    )


@router.get("/search", response_model=EntityListResponse)
async def search_entities(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    模糊搜索实体名或描述
    """
    pattern = f"%{q}%"
    query = db.query(Entity).filter(
        or_(Entity.name.ilike(pattern), Entity.description.ilike(pattern))
    )
    total = query.count()
    items = (
        query.order_by(Entity.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return EntityListResponse(
        total=total,
        items=[EntityResponse(**e.to_dict()) for e in items],
        page=page,
        page_size=page_size,
    )


@router.get("/types", response_model=EntityStatsResponse)
async def get_entity_stats(db: Session = Depends(get_db)):
    """
    实体类型分布统计
    """
    rows = (
        db.query(Entity.type, func.count(Entity.id).label("count"))
        .group_by(Entity.type)
        .order_by(func.count(Entity.id).desc())
        .all()
    )
    total = sum(r.count for r in rows)
    return EntityStatsResponse(
        total=total,
        by_type=[EntityTypeStat(type=r.type, count=r.count) for r in rows],
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: int, db: Session = Depends(get_db)):
    """
    按 ID 查询实体
    """
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"实体 {entity_id} 不存在")
    return EntityResponse(**entity.to_dict())


@router.get("/{entity_id}/degree")
async def get_entity_degree(entity_id: int, db: Session = Depends(get_db)):
    """
    查询实体的度数（关联的关系总数：出度 + 入度）
    """
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"实体 {entity_id} 不存在")

    out_degree = (
        db.query(func.count(Relationship.id))
        .filter(Relationship.source_id == entity_id)
        .scalar()
    )
    in_degree = (
        db.query(func.count(Relationship.id))
        .filter(Relationship.target_id == entity_id)
        .scalar()
    )
    return {
        "entity_id": entity_id,
        "name": entity.name,
        "out_degree": out_degree or 0,
        "in_degree": in_degree or 0,
        "total_degree": (out_degree or 0) + (in_degree or 0),
    }
