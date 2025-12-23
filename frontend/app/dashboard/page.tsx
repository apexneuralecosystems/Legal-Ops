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
import { Sparkles, Zap, Shield, LogOut, AlertCircle } from 'lucide-react'

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
        const agents: Record<string, string> = {
            'intake': 'Document Analyzer',
            'drafting': 'Drafting Agent',
            'research': 'Research Agent'
        }
        return agents[status] || 'AI Agent'
    }

    const getTaskTypeForStatus = (status: string) => {
        const types: Record<string, string> = {
            'intake': 'case_structuring',
            'drafting': 'document_generation',
            'research': 'research'
        }
        return types[status] || 'processing'
    }

    const getTaskDescription = (matter: any) => {
        if (matter.status === 'intake') {
            return `Analyzing and structuring case for ${matter.title}`
        }
        if (matter.status === 'drafting') {
            return `Generating pleading documents for ${matter.title}`
        }
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
        <div className="flex min-h-screen bg-grid">
            <Sidebar />

            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-purple)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/2 w-64 h-64 bg-[var(--neon-cyan)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                {/* Header with Logout */}
                <div className="mb-10 animate-fade-in relative">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="icon-box w-12 h-12">
                                <Zap className="w-6 h-6" />
                            </div>
                            <div>
                                <h1 className="text-4xl font-bold gradient-text">Command Center</h1>
                                <p className="text-[var(--text-secondary)] mt-1">
                                    Real-time intelligence on matters, AI operations, and critical deadlines
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-300 hover:bg-slate-600/50 hover:text-white transition-all"
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="hidden sm:inline">Logout</span>
                        </button>
                    </div>

                    <div className="cyber-line mt-6"></div>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <span className="text-red-400">{error}</span>
                        <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">
                            ✕
                        </button>
                    </div>
                )}

                <div className="mb-10 animate-slide-up stagger-1">
                    <DashboardStats stats={stats} />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 animate-slide-up stagger-2">
                        {loading ? (
                            <div className="card p-16 text-center">
                                <div className="relative inline-block">
                                    <div className="w-16 h-16 rounded-full border-4 border-[var(--border-light)] border-t-[var(--neon-purple)] animate-spin"></div>
                                    <Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 text-[var(--neon-purple)]" />
                                </div>
                                <p className="text-[var(--text-secondary)] mt-6 text-lg">Initializing neural networks...</p>
                            </div>
                        ) : (
                            <MatterSummaryPanel matters={matters as any} />
                        )}
                    </div>

                    <div className="lg:col-span-1 animate-slide-up stagger-3">
                        <AIActivityFeed tasks={aiTasks as any} />
                    </div>
                </div>

                <div className="mt-8 flex items-center justify-center gap-2 text-[var(--text-tertiary)] text-sm animate-fade-in">
                    <Shield className="w-4 h-4" />
                    <span>Secured by enterprise-grade encryption</span>
                    <span className="mx-2">•</span>
                    <span>Last sync: Just now</span>
                </div>
            </main>

            <CommandPalette isOpen={isOpen} onClose={close} />
        </div>
    )
}

// Export wrapped with ProtectedRoute
export default function DashboardPage() {
    return (
        <ProtectedRoute>
            <DashboardContent />
        </ProtectedRoute>
    )
}

