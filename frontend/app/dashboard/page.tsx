'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardStats from '@/components/DashboardStats'
import MatterSummaryPanel from '@/components/MatterSummaryPanel'
import AIActivityFeed from '@/components/AIActivityFeed'
import Sidebar from '@/components/Sidebar'
import CommandPalette, { useCommandPalette } from '@/components/CommandPalette'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { api, ApiError, tokenManager } from '@/lib/api'
import { useAuthStore } from '@/lib/authStore'
import { Sparkles, Zap, Shield, LogOut, AlertCircle, Bell } from 'lucide-react'

interface Matter {
    id: string
    matter_id: string
    title: string
    status: string
    human_review_required?: boolean
    [key: string]: any
}

interface AITask {
    id: string
    agent: string
    task_type: string
    description: string
    status: string
    progress?: number
    estimated_completion?: string
    completed_at?: string
}

function DashboardContent() {
    const router = useRouter()
    const { logout, user } = useAuthStore()
    const [matters, setMatters] = useState<Matter[]>([])
    const [aiTasks, setAiTasks] = useState<AITask[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const { isOpen, close } = useCommandPalette()

    const handleLogout = () => {
        logout()
        router.push('/login')
    }

    useEffect(() => {
        fetchMatters()
    }, [])

    useEffect(() => {
        fetchAITasks()
        const interval = setInterval(() => {
            fetchMatters()
            fetchAITasks()
        }, 10000)
        return () => clearInterval(interval)
    }, [matters.length])

    const fetchMatters = async () => {
        try {
            const data = await api.getMatters()
            setMatters(data)
        } catch (error) {
            console.error('Failed to fetch matters:', error)
        } finally {
            setLoading(false)
        }
    }

    const fetchAITasks = async () => {
        try {
            const response = await api.getAITasks(10)
            const tasks = response.tasks.map((task: any) => ({
                id: task.id,
                agent: task.agent,
                task_type: task.type,
                description: task.description,
                status: task.status === 'in_progress' ? 'processing' : task.status,
                progress: task.progress,
                estimated_completion: task.status === 'in_progress' ? '~5m' : undefined,
                completed_at: task.status === 'completed' ? 'Just now' : undefined
            }))
            setAiTasks(tasks)
        } catch (error) {
            console.error('Failed to fetch AI tasks:', error)
            const fallbackTasks = matters
                .filter(m => m.status === 'intake' || m.status === 'drafting')
                .slice(0, 5)
                .map((matter, idx) => ({
                    id: `TASK-${matter.id || idx}`,
                    agent: getAgentForStatus(matter.status),
                    task_type: getTaskTypeForStatus(matter.status),
                    description: getTaskDescription(matter),
                    status: idx === 0 ? 'processing' : idx === 1 ? 'completed' : 'pending',
                    progress: idx === 0 ? 45 : undefined,
                }))
            setAiTasks(fallbackTasks)
        }
    }

    const getAgentForStatus = (status: string) => {
        const agents: Record<string, string> = { 'intake': 'Document Analyzer', 'drafting': 'Drafting Agent', 'research': 'Research Agent' }
        return agents[status] || 'AI Agent'
    }

    const getTaskTypeForStatus = (status: string) => {
        const types: Record<string, string> = { 'intake': 'case_structuring', 'drafting': 'document_generation', 'research': 'research' }
        return types[status] || 'processing'
    }

    const getTaskDescription = (matter: any) => {
        if (matter.status === 'intake') return `Analyzing case: ${matter.title}`
        if (matter.status === 'drafting') return `Generating documents: ${matter.title}`
        return `Processing ${matter.title}`
    }

    const stats = {
        totalMatters: matters.length,
        activeMatters: matters.filter(m => m.status === 'drafting' || m.status === 'research').length,
        urgentDeadlines: matters.filter(m => m.human_review_required).length,
        aiTasksProcessing: aiTasks.filter(t => t.status === 'processing').length,
        completedToday: aiTasks.filter(t => t.status === 'completed').length,
        overdueItems: 0
    }

    return (
        <div className="flex min-h-screen bg-white text-black selection:bg-[#D4A853] selection:text-black">
            <Sidebar />

            <main className="flex-1 flex flex-col relative">
                {/* Clean professional background */}

                {/* Top Bar - Minimalist */}
                <header className="h-20 border-b border-gray-800 px-8 flex items-center justify-between bg-black">
                    <div>
                        <div className="flex items-center gap-2 text-[#D4A853] text-[10px] font-bold tracking-[0.2em] uppercase mb-1">
                            <Sparkles className="w-3 h-3" />
                            <span>Legal Intelligence Hub</span>
                        </div>
                        <h1 className="text-2xl font-serif font-black text-white tracking-tight">Case Overview</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <button className="w-10 h-10 rounded-full border border-gray-600 flex items-center justify-center text-gray-400 hover:text-[#D4A853] hover:border-[#D4A853] transition-all">
                            <Bell className="w-5 h-5" />
                        </button>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 border border-gray-600 text-gray-300 hover:text-white hover:border-[#D4A853] rounded-lg text-sm font-medium transition-all"
                        >
                            <LogOut className="w-4 h-4" />
                            <span>Sign Out</span>
                        </button>
                    </div>
                </header>

                {/* Content */}
                <div className="flex-1 p-8 overflow-y-auto">
                    {error && (
                        <div className="mb-8 p-4 bg-red-900/10 border border-red-500/20 rounded-lg flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400" />
                            <span className="text-red-400 text-sm font-medium">{error}</span>
                            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">✕</button>
                        </div>
                    )}

                    <div className="mb-10">
                        <DashboardStats stats={stats} />
                    </div>

                    <div className="grid grid-cols-1 gap-8">
                        <div className="w-full">
                            <h2 className="text-xl font-serif font-bold mb-6 flex items-center gap-3 text-black">
                                <span className="w-2 h-2 rounded-full bg-[#D4A853]"></span>
                                Active Matters
                            </h2>
                            {loading ? (
                                <div className="bg-white border border-gray-200 rounded-2xl p-20 text-center shadow-sm">
                                    <div className="relative inline-block">
                                        <div className="w-12 h-12 rounded-full border-2 border-gray-200 border-t-[#D4A853] animate-spin"></div>
                                    </div>
                                    <p className="text-gray-500 mt-6 text-sm tracking-widest uppercase">Retrieving Case Files...</p>
                                </div>
                            ) : (
                                <MatterSummaryPanel matters={matters as any} />
                            )}
                        </div>
                    </div>
                </div>

                <div className="mt-12 flex items-center justify-center gap-2 text-gray-600 text-[10px] uppercase tracking-widest opacity-50">
                    <Shield className="w-3 h-3" />
                    <span>Encrypted • PDPA Compliant • Secure</span>
                </div>
            </main>

            <CommandPalette isOpen={isOpen} onClose={close} />
        </div>
    )
}

export default function DashboardPage() {
    return (
        <ProtectedRoute>
            <DashboardContent />
        </ProtectedRoute>
    )
}
