/**
 * /graph —— 知识图谱可视化页面
 *
 * 三种模式（互斥）：
 *  1) overview —— 图谱总览：统计数据 + 实体类型分布 + 关系类型分布 + 实体类型图例
 *  2) subgraph —— 子图模式：选中心实体 + 扩展深度，画力导向图
 *  3) path     —— 寻路模式：起 + 终，画高亮最短路径
 */

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ForceGraphView, { FGLink, FGNode } from '../components/graph/ForceGraphView'
import { TYPE_COLORS, DEFAULT_NODE_COLOR } from '../components/graph/constants'
import {
    Entity,
    getGraphOverview,
    getEntityTypes,
    getSubgraph,
    findPath,
    searchEntities,
    SubgraphResp,
    PathResp,
} from '../api/knowledgeGraph'

type Mode = 'overview' | 'subgraph' | 'path'

export default function GraphVisualization() {
    const [mode, setMode] = useState<Mode>('subgraph')

    return (
        <div className="min-h-[calc(100vh-4rem)] bg-slate-50">
            {/* 顶部 Tab */}
            <div className="bg-white border-b border-slate-200">
                <div className="max-w-7xl mx-auto px-6 flex items-center gap-1">
                    <TabButton active={mode === 'overview'} onClick={() => setMode('overview')}>
                        📊 图谱总览
                    </TabButton>
                    <TabButton active={mode === 'subgraph'} onClick={() => setMode('subgraph')}>
                        🕸️ 子图浏览
                    </TabButton>
                    <TabButton active={mode === 'path'} onClick={() => setMode('path')}>
                        🛤️ 路径寻路
                    </TabButton>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-6">
                {mode === 'overview' && <OverviewPanel />}
                {mode === 'subgraph' && <SubgraphPanel />}
                {mode === 'path' && <PathPanel />}
            </div>
        </div>
    )
}

/* ============== Tab Button ============== */
function TabButton({
    active,
    onClick,
    children,
}: {
    active: boolean
    onClick: () => void
    children: React.ReactNode
}) {
    return (
        <button
            onClick={onClick}
            className={
                'px-4 py-3 text-sm font-medium border-b-2 transition-colors ' +
                (active
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800')
            }
        >
            {children}
        </button>
    )
}

/* ============== Overview Panel ============== */
function OverviewPanel() {
    const overview = useQuery({ queryKey: ['graph-overview'], queryFn: getGraphOverview })
    const types = useQuery({ queryKey: ['entity-types'], queryFn: getEntityTypes })

    if (overview.isLoading || types.isLoading) {
        return <Skeleton />
    }
    if (overview.error || types.error) {
        return <ErrorBox err={overview.error ?? types.error} />
    }

    const o = overview.data!
    const t = types.data!
    const maxTypeCount = Math.max(...t.by_type.map(x => x.count), 1)

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800">图谱总览</h2>

            {/* 数字卡片 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="实体总数" value={o.entity_total} color="primary" />
                <StatCard label="关系总数" value={o.relationship_total} color="emerald" />
                <StatCard label="实体类型数" value={o.entity_types.length} color="violet" />
                <StatCard label="关系类型数" value={o.top_relationship_types.length} color="amber" />
            </div>

            {/* 实体类型分布 */}
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">实体类型分布</h3>
                <div className="space-y-2">
                    {t.by_type.map(item => (
                        <div key={item.type} className="flex items-center gap-3">
                            <div className="w-32 text-sm text-slate-600 font-mono">{item.type}</div>
                            <div className="flex-1 h-6 bg-slate-100 rounded relative overflow-hidden">
                                <div
                                    className="h-full rounded transition-all"
                                    style={{
                                        width: `${(item.count / maxTypeCount) * 100}%`,
                                        backgroundColor: TYPE_COLORS[item.type] ?? DEFAULT_NODE_COLOR,
                                    }}
                                />
                            </div>
                            <div className="w-16 text-right text-sm text-slate-700 font-mono">
                                {item.count}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 关系类型分布 */}
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">关系类型分布（Top 20）</h3>
                {o.top_relationship_types.length === 0 ? (
                    <p className="text-slate-500 text-sm">暂无数据</p>
                ) : (
                    <div className="space-y-2">
                        {o.top_relationship_types.map(item => (
                            <div key={item.relation_type} className="flex items-center gap-3">
                                <div className="w-40 text-sm text-slate-600 font-mono">
                                    {item.relation_type}
                                </div>
                                <div className="flex-1 h-6 bg-slate-100 rounded relative overflow-hidden">
                                    <div
                                        className="h-full rounded bg-primary-500 transition-all"
                                        style={{
                                            width: `${(item.count / o.top_relationship_types[0].count) * 100}%`,
                                        }}
                                    />
                                </div>
                                <div className="w-16 text-right text-sm text-slate-700 font-mono">
                                    {item.count}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* 图例 */}
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-3">节点配色图例</h3>
                <div className="flex flex-wrap gap-3">
                    {Object.entries(TYPE_COLORS).map(([type, color]) => (
                        <div key={type} className="flex items-center gap-2 text-sm">
                            <span
                                className="inline-block w-4 h-4 rounded-full"
                                style={{ backgroundColor: color }}
                            />
                            <span className="text-slate-700 font-mono">{type}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

/* ============== Subgraph Panel ============== */
function SubgraphPanel() {
    const [centerId, setCenterId] = useState<number | ''>(696)
    const [depth, setDepth] = useState(1)
    const [maxNodes, setMaxNodes] = useState(100)
    const [submitted, setSubmitted] = useState<{ id: number; depth: number; max: number } | null>(
        { id: 696, depth: 1, max: 100 },
    )

    const { data, isLoading, error } = useQuery({
        queryKey: ['subgraph', submitted?.id, submitted?.depth, submitted?.max],
        queryFn: () => getSubgraph(submitted!.id, submitted!.depth, submitted!.max),
        enabled: !!submitted,
    })

    const onClickNode = (n: FGNode) => {
        /* 点击节点 → 重新以该节点为中心 */
        setCenterId(n.id)
        setSubmitted({ id: n.id, depth, max: maxNodes })
    }

    return (
        <div className="grid grid-cols-12 gap-6">
            {/* 控制面板 */}
            <aside className="col-span-12 md:col-span-3 space-y-4">
                <h2 className="text-xl font-bold text-slate-800">子图浏览</h2>

                <EntitySearchPicker
                    label="中心实体"
                    value={centerId}
                    onChange={id => setCenterId(id)}
                    placeholder="搜索实体名 / ID"
                />

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        扩展深度: <span className="font-mono text-primary-600">{depth}</span>
                    </label>
                    <input
                        type="range"
                        min={1}
                        max={3}
                        step={1}
                        value={depth}
                        onChange={e => setDepth(Number(e.target.value))}
                        className="w-full"
                    />
                    <p className="text-xs text-slate-500 mt-1">1 = 直接邻居, 2 = 二跳, 3 = 三跳</p>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        最大节点数: <span className="font-mono text-primary-600">{maxNodes}</span>
                    </label>
                    <input
                        type="range"
                        min={20}
                        max={500}
                        step={20}
                        value={maxNodes}
                        onChange={e => setMaxNodes(Number(e.target.value))}
                        className="w-full"
                    />
                </div>

                <button
                    onClick={() => {
                        if (centerId) setSubmitted({ id: Number(centerId), depth, max: maxNodes })
                    }}
                    disabled={!centerId || isLoading}
                    className="w-full bg-primary-500 hover:bg-primary-600 disabled:bg-slate-300 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                    {isLoading ? '加载中…' : '🔄 加载子图'}
                </button>

                {data && (
                    <div className="bg-slate-50 rounded-lg p-3 text-sm space-y-1 border border-slate-200">
                        <div className="text-slate-600">
                            中心: <span className="font-semibold text-slate-800">{data.center_entity.name}</span>
                        </div>
                        <div className="text-slate-600">节点: {data.total_nodes}</div>
                        <div className="text-slate-600">边: {data.total_links}</div>
                        <div className="text-xs text-slate-500 mt-2">
                            💡 点击画布上的节点可切换中心
                        </div>
                    </div>
                )}
            </aside>

            {/* 画布 */}
            <main className="col-span-12 md:col-span-9">
                {isLoading && <Skeleton />}
                {error && <ErrorBox err={error} />}
                {data && !isLoading && <SubgraphGraph data={data} onClickNode={onClickNode} />}
            </main>
        </div>
    )
}

function SubgraphGraph({ data, onClickNode }: { data: SubgraphResp; onClickNode: (n: FGNode) => void }) {
    const { nodes, links } = useMemo(() => {
        const ns: FGNode[] = data.nodes.map(n => ({
            id: n.id,
            name: n.name,
            type: n.type,
            degree: n.degree,
            isCenter: n.id === data.center_entity.id,
        }))
        const ls: FGLink[] = data.links.map(l => ({
            source: l.source,
            target: l.target,
            relation_type: l.relation_type,
            weight: l.weight,
        }))
        return { nodes: ns, links: ls }
    }, [data])

    return <ForceGraphView nodes={nodes} links={links} height={680} onNodeClick={onClickNode} />
}

/* ============== Path Panel ============== */
function PathPanel() {
    const [sourceId, setSourceId] = useState<number | ''>(696)
    const [targetId, setTargetId] = useState<number | ''>(720)
    const [maxDepth, setMaxDepth] = useState(4)
    const [submitted, setSubmitted] = useState<{ s: number; t: number; d: number } | null>(null)

    const { data, isLoading, error } = useQuery({
        queryKey: ['path', submitted?.s, submitted?.t, submitted?.d],
        queryFn: () => findPath(submitted!.s, submitted!.t, submitted!.d),
        enabled: !!submitted,
    })

    return (
        <div className="grid grid-cols-12 gap-6">
            <aside className="col-span-12 md:col-span-3 space-y-4">
                <h2 className="text-xl font-bold text-slate-800">路径寻路</h2>

                <EntitySearchPicker
                    label="起点实体"
                    value={sourceId}
                    onChange={id => setSourceId(id)}
                    placeholder="起点"
                />

                <EntitySearchPicker
                    label="终点实体"
                    value={targetId}
                    onChange={id => setTargetId(id)}
                    placeholder="终点"
                />

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        最大深度: <span className="font-mono text-primary-600">{maxDepth}</span>
                    </label>
                    <input
                        type="range"
                        min={1}
                        max={6}
                        step={1}
                        value={maxDepth}
                        onChange={e => setMaxDepth(Number(e.target.value))}
                        className="w-full"
                    />
                </div>

                <button
                    onClick={() => {
                        if (sourceId && targetId) {
                            setSubmitted({ s: Number(sourceId), t: Number(targetId), d: maxDepth })
                        }
                    }}
                    disabled={!sourceId || !targetId || isLoading}
                    className="w-full bg-primary-500 hover:bg-primary-600 disabled:bg-slate-300 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                    {isLoading ? '搜索中…' : '🔍 寻找最短路径'}
                </button>

                {data && (
                    <div className="bg-slate-50 rounded-lg p-3 text-sm space-y-1 border border-slate-200">
                        {data.found ? (
                            <>
                                <div className="text-emerald-600 font-semibold">✅ 找到路径</div>
                                <div className="text-slate-600">跳数: {data.length}</div>
                                <div className="text-slate-600">节点: {data.nodes?.length ?? 0}</div>
                                <div className="text-slate-600">边: {data.links?.length ?? 0}</div>
                            </>
                        ) : (
                            <div className="text-amber-600">
                                ⚠️ {data.message ?? '未找到路径'}
                            </div>
                        )}
                    </div>
                )}
            </aside>

            <main className="col-span-12 md:col-span-9">
                {!submitted && (
                    <div className="bg-white rounded-lg border border-dashed border-slate-300 p-12 text-center text-slate-500">
                        <div className="text-4xl mb-3">🛤️</div>
                        <p>选择起点与终点，点击「寻找最短路径」</p>
                    </div>
                )}
                {isLoading && <Skeleton />}
                {error && <ErrorBox err={error} />}
                {data && data.found && data.nodes && data.links && (
                    <PathGraph data={data} />
                )}
            </main>
        </div>
    )
}

function PathGraph({ data }: { data: PathResp }) {
    const { nodes, links } = useMemo(() => {
        const ns: FGNode[] = (data.nodes ?? []).map((n, i) => ({
            id: n.id,
            name: n.name,
            type: n.type,
            degree: 0,
            isCenter: i === 0 || i === (data.nodes?.length ?? 0) - 1,
        }))
        const ls: FGLink[] = (data.links ?? []).map(l => ({
            source: l.source_id,
            target: l.target_id,
            relation_type: l.relation_type,
            weight: l.weight,
            onPath: true,
        }))
        return { nodes: ns, links: ls }
    }, [data])

    return <ForceGraphView nodes={nodes} links={links} height={680} />
}

/* ============== Entity Picker (with search) ============== */
function EntitySearchPicker({
    label,
    value,
    onChange,
    placeholder,
}: {
    label: string
    value: number | ''
    onChange: (id: number) => void
    placeholder?: string
}) {
    const [query, setQuery] = useState('')
    const [open, setOpen] = useState(false)

    const { data } = useQuery({
        queryKey: ['entity-search', query],
        queryFn: () => searchEntities(query, 10),
        enabled: query.length > 0,
    })

    return (
        <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
            {value !== '' && (
                <div className="mb-1 flex items-center gap-1 text-xs bg-primary-50 text-primary-700 px-2 py-1 rounded border border-primary-200">
                    <span className="font-mono">#{value}</span>
                    <button
                        onClick={() => onChange(0)}
                        className="ml-auto text-primary-400 hover:text-primary-600"
                        type="button"
                    >
                        ×
                    </button>
                </div>
            )}
            <input
                type="text"
                placeholder={placeholder}
                value={query}
                onChange={e => {
                    setQuery(e.target.value)
                    setOpen(true)
                }}
                onFocus={() => setOpen(true)}
                onBlur={() => setTimeout(() => setOpen(false), 200)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
            {open && data && data.items.length > 0 && (
                <div className="mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {data.items.map((it: Entity) => (
                        <button
                            key={it.id}
                            type="button"
                            onMouseDown={() => {
                                onChange(it.id)
                                setQuery('')
                                setOpen(false)
                            }}
                            className="w-full text-left px-3 py-2 hover:bg-slate-50 border-b border-slate-100 last:border-0"
                        >
                            <div className="text-sm font-medium text-slate-800 truncate">{it.name}</div>
                            <div className="text-xs text-slate-500 font-mono">
                                #{it.id} · {it.type}
                            </div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}

/* ============== UI atoms ============== */
function StatCard({
    label,
    value,
    color,
}: {
    label: string
    value: number
    color: 'primary' | 'emerald' | 'violet' | 'amber'
}) {
    const colorMap = {
        primary: 'bg-primary-50 text-primary-700 border-primary-200',
        emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        violet: 'bg-violet-50 text-violet-700 border-violet-200',
        amber: 'bg-amber-50 text-amber-700 border-amber-200',
    }
    return (
        <div className={`rounded-lg border p-4 ${colorMap[color]}`}>
            <div className="text-sm opacity-80">{label}</div>
            <div className="text-3xl font-bold mt-1">{value.toLocaleString()}</div>
        </div>
    )
}

function Skeleton() {
    return (
        <div className="animate-pulse bg-white rounded-lg border border-slate-200 p-12 text-center text-slate-400">
            加载中…
        </div>
    )
}

function ErrorBox({ err }: { err: unknown }) {
    const msg = err instanceof Error ? err.message : String(err)
    return (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
            <div className="font-semibold mb-1">❌ 出错了</div>
            <div className="font-mono text-xs">{msg}</div>
        </div>
    )
}
