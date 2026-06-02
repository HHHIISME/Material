"""
图谱查询 API
提供整图查询（用于图谱可视化）、以实体为中心的子图展开
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge_graph import Entity, Relationship
from app.api.v1.schemas.kg import (
    SubgraphResponse,
    GraphNode,
    GraphLink,
    EntityResponse,
    RelationshipResponse,
)

router = APIRouter(prefix="/graph", tags=["知识图谱-图谱"])


@router.get("/overview")
async def get_graph_overview(db: Session = Depends(get_db)):
    """
    图谱总览：实体总数、关系总数、类型分布
    """
    entity_total = db.query(func.count(Entity.id)).scalar() or 0
    rel_total = db.query(func.count(Relationship.id)).scalar() or 0

    entity_types = (
        db.query(Entity.type, func.count(Entity.id).label("count"))
        .group_by(Entity.type)
        .all()
    )
    rel_types = (
        db.query(Relationship.relation_type, func.count(Relationship.id).label("count"))
        .group_by(Relationship.relation_type)
        .order_by(func.count(Relationship.id).desc())
        .limit(20)
        .all()
    )

    return {
        "entity_total": entity_total,
        "relationship_total": rel_total,
        "entity_types": [{"type": t.type, "count": t.count} for t in entity_types],
        "top_relationship_types": [
            {"relation_type": t.relation_type, "count": t.count} for t in rel_types
        ],
    }


@router.get("/subgraph/{entity_id}", response_model=SubgraphResponse)
async def get_subgraph(
    entity_id: int,
    depth: int = Query(1, ge=1, le=3, description="扩展深度（1-3）"),
    max_nodes: int = Query(100, ge=1, le=500, description="最大节点数"),
    db: Session = Depends(get_db),
):
    """
    以某实体为中心，扩展 depth 跳的子图（用于可视化）

    返回 nodes + links，前端可直接用 react-force-graph / cytoscape 渲染
    """
    center = db.query(Entity).filter(Entity.id == entity_id).first()
    if not center:
        raise HTTPException(status_code=404, detail=f"实体 {entity_id} 不存在")

    # 用 BFS 收集节点
    visited_ids = {entity_id}
    current_ids = {entity_id}
    collected_rels: list[Relationship] = []

    for _ in range(depth):
        if not current_ids:
            break
        rels = (
            db.query(Relationship)
            .filter(
                or_(
                    Relationship.source_id.in_(current_ids),
                    Relationship.target_id.in_(current_ids),
                )
            )
            .all()
        )
        next_ids: set[int] = set()
        for r in rels:
            collected_rels.append(r)
            for nid in (r.source_id, r.target_id):
                if nid not in visited_ids:
                    next_ids.add(nid)
        visited_ids.update(next_ids)
        current_ids = next_ids
        if len(visited_ids) >= max_nodes:
            break

    # 截断到 max_nodes
    if len(visited_ids) > max_nodes:
        # 优先保留与中心实体直接相连的
        direct_neighbors = set()
        for r in collected_rels:
            if r.source_id == entity_id:
                direct_neighbors.add(r.target_id)
            elif r.target_id == entity_id:
                direct_neighbors.add(r.source_id)
        kept = {entity_id} | direct_neighbors
        for r in collected_rels:
            if len(kept) >= max_nodes:
                break
            for nid in (r.source_id, r.target_id):
                if nid not in kept and (r.source_id in kept or r.target_id in kept):
                    kept.add(nid)
        visited_ids = kept

    # 取出最终节点
    nodes_db = db.query(Entity).filter(Entity.id.in_(visited_ids)).all()
    degree_map: dict[int, int] = {n.id: 0 for n in nodes_db}
    final_links: list[GraphLink] = []
    for r in collected_rels:
        if r.source_id in visited_ids and r.target_id in visited_ids:
            final_links.append(
                GraphLink(
                    source=r.source_id,
                    target=r.target_id,
                    relation_type=r.relation_type,
                    weight=r.weight,
                )
            )
            degree_map[r.source_id] = degree_map.get(r.source_id, 0) + 1
            degree_map[r.target_id] = degree_map.get(r.target_id, 0) + 1

    nodes = [
        GraphNode(
            id=n.id,
            name=n.name,
            type=n.type,
            degree=degree_map.get(n.id, 0),
        )
        for n in nodes_db
    ]

    return SubgraphResponse(
        center_entity=EntityResponse(**center.to_dict()),
        nodes=nodes,
        links=final_links,
        depth=depth,
        total_nodes=len(nodes),
        total_links=len(final_links),
    )


@router.get("/path")
async def find_path(
    source_id: int = Query(..., description="起点实体 ID"),
    target_id: int = Query(..., description="终点实体 ID"),
    max_depth: int = Query(4, ge=1, le=6, description="最大搜索深度"),
    db: Session = Depends(get_db),
):
    """
    在两个实体之间寻找最短路径（BFS）

    返回路径上的节点和关系
    """
    if source_id == target_id:
        return {"nodes": [], "links": [], "found": False, "message": "source 与 target 相同"}

    # 邻接表（无向）
    adj: dict[int, list[tuple[int, Relationship]]] = {}
    rels = db.query(Relationship).all()
    for r in rels:
        adj.setdefault(r.source_id, []).append((r.target_id, r))
        adj.setdefault(r.target_id, []).append((r.source_id, r))

    # BFS
    from collections import deque
    queue = deque([(source_id, [source_id])])
    visited = {source_id}
    parent: dict[int, tuple[int, Relationship]] = {}

    found = False
    while queue:
        cur, path = queue.popleft()
        if cur == target_id:
            found = True
            break
        if len(path) > max_depth:
            continue
        for nb, rel in adj.get(cur, []):
            if nb not in visited:
                visited.add(nb)
                parent[nb] = (cur, rel)
                queue.append((nb, path + [nb]))

    if not found:
        return {"nodes": [], "links": [], "found": False, "message": f"深度 {max_depth} 内未找到路径"}

    # 还原路径
    node_path = [target_id]
    link_path: list[Relationship] = []
    cur = target_id
    while cur in parent:
        prev, rel = parent[cur]
        node_path.append(prev)
        link_path.append(rel)
        cur = prev
    node_path.reverse()
    link_path.reverse()

    nodes_db = db.query(Entity).filter(Entity.id.in_(node_path)).all()
    nodes_map = {n.id: n for n in nodes_db}

    return {
        "found": True,
        "length": len(node_path) - 1,
        "nodes": [EntityResponse(**nodes_map[i].to_dict()).model_dump() for i in node_path if i in nodes_map],
        "links": [RelationshipResponse(**r.to_dict()).model_dump() for r in link_path],
    }
