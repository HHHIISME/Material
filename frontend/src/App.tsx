import { useState } from 'react'

function App() {
    const [count, setCount] = useState(0)

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
            <div className="text-center">
                <h1 className="text-4xl font-bold text-primary-600 mb-4">
                    材料学院智能学习平台
                </h1>
                <p className="text-lg text-gray-600 mb-8">
                    Material Science Intelligent Learning Platform
                </p>
                <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
                    <div className="card">
                        <button
                            onClick={() => setCount(count => count + 1)}
                            className="bg-primary-500 hover:bg-primary-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                        >
                            count is {count}
                        </button>
                        <p className="mt-4 text-gray-500">
                            编辑 <code className="bg-gray-100 px-2 py-1 rounded">src/App.tsx</code> 并保存以测试 HMR
                        </p>
                    </div>
                </div>
                <p className="mt-6 text-gray-400">
                    FastAPI + React + TypeScript + Tailwind CSS
                </p>
            </div>
        </div>
    )
}

export default App
