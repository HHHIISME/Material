/**
 * 实体类型 → 节点配色
 * 选用 Tailwind 调色板的 500 色阶（对比度好，在白底/暗底都清晰）
 */
export const TYPE_COLORS: Record<string, string> = {
    MATERIAL: '#3b82f6', // primary-500 (蓝)
    PROPERTY: '#10b981', // emerald-500
    PROCESS: '#f59e0b', // amber-500
    APPLICATION: '#ef4444', // red-500
    TECHNOLOGY: '#8b5cf6', // violet-500
    STRUCTURE: '#06b6d4', // cyan-500
    EQUIPMENT: '#84cc16', // lime-500
    SCIENCE: '#ec4899', // pink-500
    RESEARCH: '#f97316', // orange-500
    TEMPERATURE: '#f43f5e', // rose-500
    GEO: '#14b8a6', // teal-500
    ENGINEERING: '#a855f7', // purple-500
    FILE: '#6b7280', // gray-500
    FILE_PATTERN: '#9ca3af', // gray-400
}

export const DEFAULT_NODE_COLOR = '#94a3b8' // slate-400

export function colorFor(type: string): string {
    return TYPE_COLORS[type] ?? DEFAULT_NODE_COLOR
}

/** 度数 → 节点半径（视觉上突出中心节点） */
export function radiusFor(degree: number, isCenter = false): number {
    if (isCenter) return 12
    if (degree >= 5) return 7
    if (degree >= 2) return 5
    return 3.5
}
