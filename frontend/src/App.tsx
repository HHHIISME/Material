import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import GraphVisualization from './pages/GraphVisualization'

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
})

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <div className="min-h-screen bg-slate-50">
                    <TopBar />
                    <Routes>
                        <Route path="/" element={<Navigate to="/graph" replace />} />
                        <Route path="/graph" element={<GraphVisualization />} />
                        <Route path="*" element={<NotFound />} />
                    </Routes>
                </div>
            </BrowserRouter>
        </QueryClientProvider>
    )
}

function TopBar() {
    const navItem = ({ isActive }: { isActive: boolean }) =>
        'px-3 py-1.5 text-sm font-medium rounded-md transition-colors ' +
        (isActive
            ? 'bg-primary-100 text-primary-700'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800')

    return (
        <header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 shadow-sm">
            <div className="flex items-center gap-2 mr-8">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-md flex items-center justify-center text-white font-bold">
                    M
                </div>
                <div>
                    <div className="text-base font-semibold text-slate-800 leading-tight">
                        材料学院智能学习平台
                    </div>
                    <div className="text-[10px] text-slate-500 leading-tight">
                        Material Science Learning Platform
                    </div>
                </div>
            </div>

            <nav className="flex items-center gap-1">
                <NavLink to="/graph" className={navItem}>
                    🕸️ 知识图谱
                </NavLink>
            </nav>

            <div className="ml-auto text-xs text-slate-400 font-mono">v0.1.0</div>
        </header>
    )
}

function NotFound() {
    return (
        <div className="min-h-[60vh] flex items-center justify-center">
            <div className="text-center">
                <div className="text-6xl mb-4">🧭</div>
                <div className="text-xl text-slate-700">页面不存在</div>
                <NavLink to="/graph" className="text-primary-600 hover:underline mt-2 inline-block">
                    返回图谱
                </NavLink>
            </div>
        </div>
    )
}

export default App
