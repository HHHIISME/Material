/**
 * 知识图谱 API 客户端
 * 与 backend/app/api/v1/{entities,relationships,graph}.py 对应
 */

import axios from 'axios'

const http = axios.create({
    baseURL: '/api/v1',
    timeout: 15000,
})

/* ============== Types ============== */

export interface Entity {
    id: number
    name: string
    type: string
    description?: string | null
    source_doc?: string | null
    created_at?: string | null
    updated_at?: string | null
}

export interface EntityListResp {
    total: number
    items: Entity[]
    page: number
    page_size: number
}

export interface EntityTypeStat {
    type: string
    count: number
}

export interface EntityStatsResp {
    total: number
    by_type: EntityTypeStat[]
}

export interface Relationship {
    id: number
    source_id: number
    target_id: number
    source_name?: string | null
    target_name?: string | null
    relation_type: string
    description?: string | null
    weight?: number | null
    source_doc?: string | null
    created_at?: string | null
    updated_at?: string | null
}

export interface RelationshipListResp {
    total: number
    items: Relationship[]
    page: number
    page_size: number
}

export interface GraphNode {
    id: number
    name: string
    type: string
    degree: number
}

export interface GraphLink {
    source: number
    target: number
    relation_type: string
    weight?: number | null
}

export interface SubgraphResp {
    center_entity: Entity
    nodes: GraphNode[]
    links: GraphLink[]
    depth: number
    total_nodes: number
    total_links: number
}

export interface GraphOverviewResp {
    entity_total: number
    relationship_total: number
    entity_types: EntityTypeStat[]
    top_relationship_types: { relation_type: string; count: number }[]
}

export interface PathResp {
    found: boolean
    length?: number
    nodes?: Entity[]
    links?: Relationship[]
    message?: string
}

/* ============== Entities ============== */

export const listEntities = (params: {
    page?: number
    page_size?: number
    type?: string
    q?: string
} = {}) => http.get<EntityListResp>('/entities', { params }).then(r => r.data)

export const searchEntities = (q: string, limit = 20) =>
    http.get<EntityListResp>('/entities/search', { params: { q, page_size: limit } }).then(r => r.data)

export const getEntityTypes = () =>
    http.get<{ total: number; by_type: EntityTypeStat[] }>('/entities/types').then(r => r.data)

export const getEntity = (id: number) =>
    http.get<Entity>(`/entities/${id}`).then(r => r.data)

export const getEntityDegree = (id: number) =>
    http.get<{ id: number; degree: number }>(`/entities/${id}/degree`).then(r => r.data)

/* ============== Relationships ============== */

export const listRelationships = (params: {
    page?: number
    page_size?: number
    relation_type?: string
} = {}) => http.get<RelationshipListResp>('/relationships', { params }).then(r => r.data)

export const getRelationshipTypes = () =>
    http.get<{ total: number; by_type: { relation_type: string; count: number }[] }>('/relationships/types').then(r => r.data)

export const getRelationshipsByEntity = (entityId: number) =>
    http.get<RelationshipListResp>(
        `/relationships/by-entity/${entityId}`,
    ).then(r => r.data)

/* ============== Graph ============== */

export const getGraphOverview = () =>
    http.get<GraphOverviewResp>('/graph/overview').then(r => r.data)

export const getSubgraph = (entityId: number, depth = 1, maxNodes = 100) =>
    http.get<SubgraphResp>('/graph/subgraph/' + entityId, {
        params: { depth, max_nodes: maxNodes },
    }).then(r => r.data)

export const findPath = (sourceId: number, targetId: number, maxDepth = 4) =>
    http.get<PathResp>('/graph/path', {
        params: { source_id: sourceId, target_id: targetId, max_depth: maxDepth },
    }).then(r => r.data)
