'use client'

import { CheckCircle2, Loader2, Clock, Cpu, Zap, Brain, FileSearch, BookOpen, FileText, Gavel, Activity } from 'lucide-react'

interface AITask {
    id: string
    agent: string
    task_type: string
    description: string
    status: 'completed' | 'processing' | 'pending'
    progress?: number
    estimated_completion?: string
    completed_at?: string
}

interface AIActivityFeedProps {
    tasks: AITask[]
}

const taskConfig: Record<string, { icon: React.ComponentType<any>; label: string }> = {
    'document_generation': { icon: FileText, label: 'Document Gen' },
    'translation': { icon: BookOpen, label: 'Translation' },
    'clause_extraction': { icon: FileSearch, label: 'Extraction' },
    'bilingual_processing': { icon: BookOpen, label: 'Bilingual' },
    'risk_scoring': { icon: Zap, label: 'Risk Analysis' },
    'case_structuring': { icon: Brain, label: 'Structuring' },
    'research': { icon: FileSearch, label: 'Research' },
    'drafting': { icon: FileText, label: 'Drafting' },
    'evidence_building': { icon: Gavel, label: 'Evidence' },
    'hearing_prep': { icon: Gavel, label: 'Hearing' }
}

export default function AIActivityFeed({ tasks }: AIActivityFeedProps) {
    const activeTasks = tasks.filter(t => t.status === 'processing').length

    return (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden h-full shadow-sm">
            {/* Header */}
            <div className="p-5 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[var(--gold-primary)] flex items-center justify-center">
                        <Activity className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-black">AI Operations</h2>
                        <p className="text-xs text-gray-500">Real-time processing</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#D4A853]/10 border border-[#D4A853]/30">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#D4A853] animate-pulse"></div>
                    <span className="text-[10px] font-bold text-[#D4A853] tracking-wider">LIVE</span>
                </div>
            </div>

            {/* Task List */}
            <div className="max-h-[360px] overflow-y-auto">
                {tasks.length === 0 ? (
                    <div className="p-12 text-center">
                        <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center">
                            <Cpu className="w-8 h-8 text-[#D4A853]" />
                        </div>
                        <p className="text-gray-500">No active tasks</p>
                        <p className="text-xs text-gray-400 mt-1">AI agents standing by</p>
                    </div>
                ) : (
                    <div className="divide-y divide-gray-200">
                        {tasks.map((task) => {
                            const config = taskConfig[task.task_type] || { icon: Cpu, label: 'Processing' }
                            const IconComponent = config.icon

                            return (
                                <div key={task.id} className="p-4 hover:bg-white/[0.02] transition-colors">
                                    <div className="flex items-start gap-3">
                                        <div className="w-9 h-9 rounded-lg bg-gray-100 border border-gray-200 flex items-center justify-center flex-shrink-0">
                                            {task.status === 'processing' ? (
                                                <Loader2 className="w-4 h-4 text-[#D4A853] animate-spin" />
                                            ) : task.status === 'completed' ? (
                                                <CheckCircle2 className="w-4 h-4 text-[#D4A853]" />
                                            ) : (
                                                <IconComponent className="w-4 h-4 text-[#D4A853]" />
                                            )}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-sm font-medium text-black">{config.label}</span>
                                                <span className="font-mono text-[9px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                                                    {task.id}
                                                </span>
                                            </div>

                                            <p className="text-xs text-gray-500 line-clamp-1 mb-2">
                                                {task.description}
                                            </p>

                                            {task.status === 'processing' && task.progress !== undefined ? (
                                                <div>
                                                    <div className="flex items-center justify-between text-[10px] mb-1">
                                                        <span className="text-gray-600">Progress</span>
                                                        <span className="font-semibold text-[#D4A853]">{task.progress}%</span>
                                                    </div>
                                                    <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-[#D4A853] rounded-full transition-all"
                                                            style={{ width: `${task.progress}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            ) : task.status === 'completed' ? (
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#D4A853]/10 text-[#D4A853] border border-[#D4A853]/20">
                                                        ✓ Completed
                                                    </span>
                                                    {task.completed_at && (
                                                        <span className="text-[10px] text-gray-600">{task.completed_at}</span>
                                                    )}
                                                </div>
                                            ) : (
                                                <span className="text-[10px] text-gray-600 flex items-center gap-1">
                                                    <Clock className="w-3 h-3" /> Queued
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}
