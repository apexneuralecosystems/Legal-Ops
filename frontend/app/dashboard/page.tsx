'use client'

import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import DashboardStats, { StatCardItem } from '@/components/DashboardStats'
import MatterSummaryPanel from '@/components/MatterSummaryPanel'
import ResourceGrid, { AgentResource } from '@/components/ResourceGrid'
import Sidebar from '@/components/Sidebar'
import CommandPalette, { useCommandPalette } from '@/components/CommandPalette'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/authStore'
import { Bell, LogOut, Loader2, PlayCircle, ShieldCheck, Briefcase, Clock, Zap, AlertCircle, Search, FileText, Database, Bot } from 'lucide-react'
import { motion } from 'framer-motion'

interface AITask {
    id: string
    title: string
    description: string
    progress: number
    eta?: string
    status: string
}

function DashboardContent() {
    const router = useRouter()
    const { logout, user } = useAuthStore()
    const { isOpen, close } = useCommandPalette()

    // Fetch dashboard stats from backend
    const { data: backendStats } = useQuery({
        queryKey: ['mattersStats'],
        queryFn: () => api.getMattersStats(),
    })

    // Fetch matters with React Query
    const { data: matters = [], isLoading: mattersLoading } = useQuery({
        queryKey: ['matters'],
        queryFn: () => api.getMatters(),
    })

    // Fetch AI tasks with React Query
    const { data: aiTasksData } = useQuery({
        queryKey: ['aiTasks'],
        queryFn: () => api.getAITasks(10),
    })

    const aiTasks: AITask[] = (aiTasksData?.tasks || []).map((task: any) => ({
        id: task.id,
        title: task.task_type || 'System Operation',
        description: task.description,
        progress: task.progress || 0,
        eta: task.status === 'in_progress' ? '~4m' : 'Done',
        status: task.status
    }))

    // Add some mock AI tasks if empty for visualization
    const displayTasks = aiTasks.length > 0 ? aiTasks : [
        { id: '1', title: 'Document Synthesis', description: 'MTR-2026-0891', progress: 87, eta: '4 min', status: 'processing' },
        { id: '2', title: 'Legal Research', description: 'Patent Law Precedents', progress: 42, eta: '12 min', status: 'processing' },
        { id: '3', title: 'Evidence Analysis', description: 'Audio Transcription', progress: 15, eta: '18 min', status: 'queued' }
    ]

    const handleLogout = () => {
        logout()
        router.push('/login')
    }

    // Combine backend stats with frontend AI task stats
    const stats = {
        totalMatters: backendStats?.totalMatters || matters.length,
        activeMatters: backendStats?.activeMatters || matters.filter((m: any) =>
            ['drafting', 'research', 'structured', 'ready'].includes(m.status)
        ).length,
        urgentDeadlines: backendStats?.urgentDeadlines || matters.filter((m: any) =>
            m.human_review_required
        ).length,
        aiTasksProcessing: displayTasks.filter((t) => t.status === 'processing').length,
        completedToday: displayTasks.filter((t) => t.status === 'completed').length,
        overdueItems: backendStats?.overdueItems || 0
    }

    const statItems: StatCardItem[] = [
        {
            label: 'Active Matters',
            value: stats.activeMatters,
            icon: Briefcase,
            color: 'text-[#EAEAEA]',
            // Only show trend if we have historical data (mocking the logic here: if active > 0, show stable or up)
            trend: stats.activeMatters > 0 ? 'Active' : undefined,
            trendUp: stats.activeMatters > 0 ? null : undefined
        },
        {
            label: 'Urgent Deadlines',
            value: stats.urgentDeadlines,
            icon: Clock,
            color: 'text-[#C9A24D]',
            trend: stats.urgentDeadlines > 0 ? 'Due soon' : undefined,
            trendUp: stats.urgentDeadlines > 0 ? false : undefined
        },
        {
            label: 'AI Efficiency',
            value: `${Math.round((stats.aiTasksProcessing ? (stats.completedToday / (stats.aiTasksProcessing + stats.completedToday)) * 100 : 0) * 10) / 10}%`,
            icon: Zap,
            color: 'text-[#EAEAEA]',
            trend: stats.completedToday > 0 ? 'Processing' : undefined,
            trendUp: true
        },
        {
            label: 'Pending Review',
            value: stats.overdueItems,
            icon: AlertCircle,
            color: 'text-[#EAEAEA]',
            trend: stats.overdueItems > 0 ? 'Action Req' : undefined,
            trendUp: false
        }
    ]

    // Map Tasks to Agents for Resource Grid
    const agentResources: AgentResource[] = [
        {
            id: 'R-01',
            name: 'Lexis Core',
            role: 'Legal Research',
            status: displayTasks.some(t => t.title.toLowerCase().includes('research') || t.title.toLowerCase().includes('search')) ? 'ACTIVE' : 'IDLE',
            currentTask: displayTasks.find(t => t.title.toLowerCase().includes('research') || t.title.toLowerCase().includes('search'))?.description,
            efficiency: 98,
            history: [65, 75, 70, 85, 90, 88, 95, 98],
            icon: Search
        },
        {
            id: 'D-04',
            name: 'Scribe Engine',
            role: 'Drafting',
            status: displayTasks.some(t => t.title.toLowerCase().includes('document') || t.title.toLowerCase().includes('draft')) ? 'ACTIVE' : 'IDLE',
            currentTask: displayTasks.find(t => t.title.toLowerCase().includes('document') || t.title.toLowerCase().includes('draft'))?.description,
            efficiency: 95,
            history: [80, 82, 85, 80, 88, 92, 94, 95],
            icon: FileText
        },
        {
            id: 'E-09',
            name: 'Evidence Syncer',
            role: 'Discovery',
            status: displayTasks.some(t => t.title.toLowerCase().includes('evidence') || t.title.toLowerCase().includes('audio')) ? 'ACTIVE' : 'IDLE',
            currentTask: displayTasks.find(t => t.title.toLowerCase().includes('evidence') || t.title.toLowerCase().includes('audio'))?.description,
            efficiency: 92,
            history: [60, 55, 65, 70, 75, 80, 85, 92],
            icon: Database
        },
        {
            id: 'C-02',
            name: 'Compliance Guard',
            role: 'Risk Analysis',
            status: displayTasks.some(t => t.title.toLowerCase().includes('compliance') || t.title.toLowerCase().includes('risk')) ? 'ACTIVE' : 'IDLE',
            currentTask: displayTasks.find(t => t.title.toLowerCase().includes('compliance') || t.title.toLowerCase().includes('risk'))?.description,
            efficiency: 89,
            history: [88, 86, 85, 87, 88, 89, 88, 89],
            icon: Bot
        }
    ]

    if (mattersLoading) {
        return (
            <div className="flex min-h-screen bg-[#0B0B0B] items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-8 h-8 animate-spin text-[#C9A24D]" />
                    <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-[#525252]">Initializing Command Center...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen bg-[#0B0B0B] text-[#EAEAEA] selection:bg-[#C9A24D] selection:text-black font-sans">
            <Sidebar />

            <main className="flex-1 flex flex-col relative overflow-hidden bg-[#0B0B0B]">
                {/* Header */}
                <header className="px-8 py-6 flex items-center justify-between border-b border-[#333] bg-[#0B0B0B]/95 backdrop-blur z-20 sticky top-0">
                    <div>
                        <h1 className="text-2xl font-serif font-bold text-[#EAEAEA] tracking-tight">Executive Dashboard</h1>
                        <p className="text-[11px] text-[#9A9A9A] tracking-wide mt-1">Command Center — Operations Overview</p>
                    </div>

                    <div className="flex items-center gap-6">
                        <button className="relative p-2 text-[#9A9A9A] hover:text-[#C9A24D] transition-colors">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-1 right-1 w-2 h-2 bg-[#8B2E2E] rounded-full ring-2 ring-[#0B0B0B]" />
                        </button>

                        <div className="h-4 w-px bg-[#333]" />

                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 border border-[#C9A24D]/50 text-[#C9A24D] text-[10px] uppercase font-bold tracking-widest hover:bg-[#C9A24D] hover:text-black transition-all rounded-sm"
                        >
                            <LogOut className="w-3 h-3" />
                            Terminate Session
                        </button>
                    </div>
                </header>

                {/* Dashboard Content */}
                <div className="flex-1 p-8 overflow-y-auto custom-scrollbar">

                    {/* KPI Summary Cards */}
                    <DashboardStats items={statItems} />

                    {/* Main Grid */}
                    <div className="grid grid-cols-12 gap-8">

                        {/* Left: Matter Registry */}
                        <div className="col-span-12 xl:col-span-8">
                            <MatterSummaryPanel matters={matters} />
                        </div>

                        {/* Right: AI Task Queue */}
                        <div className="col-span-12 xl:col-span-4 flex flex-col gap-6">

                            {/* Resource Allocation Grid (Agent Status) */}
                            <ResourceGrid agents={agentResources} />

                            {/* System Status / Security Badge */}
                            <div className="bg-[#121212]/50 border border-[#333] border-dashed rounded-lg p-6 flex items-center gap-4 group hover:border-[#C9A24D]/30 transition-colors">
                                <div className="p-3 bg-[#1A1A1A] rounded-full group-hover:bg-[#C9A24D]/10 transition-colors">
                                    <ShieldCheck className="w-5 h-5 text-[#525252] group-hover:text-[#C9A24D] transition-colors" />
                                </div>
                                <div>
                                    <h4 className="text-xs font-bold text-[#9A9A9A] uppercase tracking-wide">Security Clearance</h4>
                                    <p className="text-[10px] text-[#525252] mt-1">Level 4: Encryption Active</p>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>

                {/* Footer Status Bar moved to Sidebar area or kept minimal here if needed, 
                    but Sidebar usually handles "System Online" now. 
                    Let's revert to a clean bottom layout. */}
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
