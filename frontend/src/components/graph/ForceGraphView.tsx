/**
 * 基于 react-force-graph-2d 的力导向图视图
 * 数据格式（来自 /graph/subgraph 或 /graph/path）：
 *   { nodes: [{id, name, type, degree}], links: [{source, target, relation_type, weight}] }
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import { colorFor, radiusFor } from './constants'

export interface FGNode {
    id: number
    name: string
    type: string
    degree: number
    /** 路径模式中标记中心节点 */
    isCenter?: boolean
    /** 力导向图内部位置（d3 模拟写入） */
    x?: number
    y?: number
    vx?: number
    vy?: number
}

export interface FGLink {
    source: number
    target: number
    relation_type: string
    weight?: number | null
    /** 路径模式中高亮 */
    onPath?: boolean
}

interface Props {
    nodes: FGNode[]
    links: FGLink[]
    height?: number
    onNodeClick?: (node: FGNode) => void
}

/** react-force-graph 内部会改写 link 的 source/target 为对象，这里做兼容 */
type RawLink = FGLink & {
    source: number | NodeObject
    target: number | NodeObject
}

export default function ForceGraphView({ nodes, links, height = 600, onNodeClick }: Props) {
    const fgRef = useRef<ForceGraphMethods | undefined>(undefined)
    const [size, setSize] = useState({ w: 800, h: height })
    const [hovered, setHovered] = useState<FGNode | null>(null)
    const containerRef = useRef<HTMLDivElement | null>(null)

    /* 监听容器宽度，自适应 */
    useEffect(() => {
        const el = containerRef.current
        if (!el) return
        const ro = new ResizeObserver(entries => {
            for (const entry of entries) {
                setSize({
                    w: Math.floor(entry.contentRect.width),
                    h: height,
                })
            }
        })
        ro.observe(el)
        return () => ro.disconnect()
    }, [height])

    /* 数据深拷贝 —— react-force-graph 会原地改 link.source/target 成对象引用 */
    const data = useMemo(() => {
        return {
            nodes: nodes.map(n => ({ ...n })),
            links: links.map(l => ({ ...l })),
        }
    }, [nodes, links])

    /* 节点绘制 —— 圆形 + 类型颜色 + 度数大小 + 中心节点加光环 */
    const drawNode = (nodeRaw: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
        const node = nodeRaw as unknown as FGNode
        const r = radiusFor(node.degree ?? 0, node.isCenter)
        const x = node.x ?? 0
        const y = node.y ?? 0
        const color = colorFor(node.type)

        /* 中心节点：白色描边光环 */
        if (node.isCenter) {
            ctx.beginPath()
            ctx.arc(x, y, r + 4 / globalScale, 0, 2 * Math.PI)
            ctx.fillStyle = 'rgba(255,255,255,0.95)'
            ctx.fill()
        }

        /* 节点主圆 */
        ctx.beginPath()
        ctx.arc(x, y, r, 0, 2 * Math.PI)
        ctx.fillStyle = color
        ctx.fill()
        ctx.strokeStyle = '#1e293b'
        ctx.lineWidth = 0.5 / globalScale
        ctx.stroke()

        /* 缩放 > 1.5 时才显示文字标签 */
        if (globalScale > 1.2) {
            const label = node.name
            const fontSize = 11 / globalScale
            ctx.font = `${fontSize}px Inter, system-ui, sans-serif`
            ctx.textAlign = 'center'
            ctx.textBaseline = 'top'
            ctx.fillStyle = '#0f172a'
            /* 描边白底，避免文字穿线 */
            ctx.strokeStyle = 'rgba(255,255,255,0.85)'
            ctx.lineWidth = 3 / globalScale
            ctx.strokeText(label, x, y + r + 1)
            ctx.fillText(label, x, y + r + 1)
        }
    }

    /* 节点悬浮提示（简易 tooltip） */
    const handleNodeHover = (node: NodeObject | null) => {
        setHovered((node as FGNode | null) ?? null)
    }

    return (
        <div ref={containerRef} className="relative w-full" style={{ height }}>
            <ForceGraph2D
                ref={fgRef}
                width={size.w}
                height={size.h}
                graphData={data}
                nodeCanvasObject={drawNode}
                nodePointerAreaPaint={(node, color, ctx) => {
                    /* 扩大点击区，节点小也能点 */
                    const n = node as unknown as FGNode
                    const r = radiusFor(n.degree ?? 0, n.isCenter)
                    ctx.fillStyle = color
                    ctx.beginPath()
                    ctx.arc(node.x ?? 0, node.y ?? 0, r + 3, 0, 2 * Math.PI)
                    ctx.fill()
                }}
                linkColor={(link: LinkObject) => {
                    const l = link as unknown as RawLink
                    return l.onPath ? '#ef4444' : 'rgba(100,116,139,0.45)'
                }}
                linkWidth={(link: LinkObject) => {
                    const l = link as unknown as RawLink
                    return l.onPath ? 2.5 : 1
                }}
                linkDirectionalArrowLength={(link: LinkObject) => {
                    const l = link as unknown as RawLink
                    return l.onPath ? 6 : 4
                }}
                linkDirectionalArrowRelPos={0.95}
                linkLabel={(link: LinkObject) => {
                    const l = link as unknown as RawLink
                    return `${l.relation_type}${l.weight ? ` (w=${l.weight})` : ''}`
                }}
                onNodeHover={handleNodeHover}
                onNodeClick={(node: NodeObject) => onNodeClick?.(node as unknown as FGNode)}
                cooldownTicks={120}
                d3AlphaDecay={0.025}
                d3VelocityDecay={0.3}
                backgroundColor="#ffffff"
            />

            {/* 悬浮 tooltip */}
            {hovered && (
                <div
                    className="pointer-events-none absolute top-2 left-2 bg-slate-900/90 text-white text-xs px-3 py-2 rounded shadow-lg max-w-xs"
                >
                    <div className="font-semibold">{hovered.name}</div>
                    <div className="opacity-75 mt-0.5">
                        {hovered.type} · 度 {hovered.degree}
                    </div>
                </div>
            )}

            {/* 节点 / 边 计数 */}
            <div className="pointer-events-none absolute bottom-2 right-2 bg-white/80 text-slate-600 text-xs px-2 py-1 rounded">
                {nodes.length} 节点 · {links.length} 边
            </div>
        </div>
    )
}
