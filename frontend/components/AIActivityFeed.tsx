'use client'

import { CheckCircle2, Loader2, Clock, Cpu, Zap, Brain, FileSearch, BookOpen, FileText, Gavel } from 'lucide-react'

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

const taskConfig: Record<string, { icon: React.ComponentType<any>; gradient: string; label: string }> = {
    'document_generation': { icon: FileText, gradient: 'from-[var(--neon-pink)] to-[var(--neon-orange)]', label: 'Document Gen' },
    'translation': { icon: BookOpen, gradient: 'from-[var(--neon-cyan)] to-[var(--neon-blue)]', label: 'Translation' },
    'clause_extraction': { icon: FileSearch, gradient: 'from-[var(--neon-purple)] to-[var(--neon-pink)]', label: 'Extraction' },
    'bilingual_processing': { icon: BookOpen, gradient: 'from-[var(--neon-green)] to-[var(--neon-cyan)]', label: 'Bilingual' },
    'risk_scoring': { icon: Zap, gradient: 'from-[var(--neon-orange)] to-[var(--neon-red)]', label: 'Risk Analysis' },
    'case_structuring': { icon: Brain, gradient: 'from-[var(--neon-purple)] to-[var(--neon-blue)]', label: 'Structuring' },
    'research': { icon: FileSearch, gradient: 'from-[var(--neon-cyan)] to-[var(--neon-green)]', label: 'Research' },
    'drafting': { icon: FileText, gradient: 'from-[var(--neon-pink)] to-[var(--neon-purple)]', label: 'Drafting' },
    'evidence_building': { icon: Gavel, gradient: 'from-[var(--neon-orange)] to-[var(--neon-yellow)]', label: 'Evidence' },
    'hearing_prep': { icon: Gavel, gradient: 'from-[var(--neon-blue)] to-[var(--neon-purple)]', label: 'Hearing' }
}

export default function AIActivityFeed({ tasks }: AIActivityFeedProps) {
    const activeTasks = tasks.filter(t => t.status === 'processing').length

    return (
        <div className="card p-6 h-full">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--neon-cyan)] to-[var(--neon-green)] flex items-center justify-center shadow-lg">
                            <Cpu className="w-6 h-6 text-white" />
                        </div>
                        {activeTasks > 0 && (
                            <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[var(--neon-green)] flex items-center justify-center text-[10px] font-bold text-black">
                                {activeTasks}
                            </span>
                        )}
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-[var(--text-primary)]">AI Operations</h2>
                        <p className="text-sm text-[var(--text-secondary)]">Neural network activity</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--status-success-bg)] border border-[var(--neon-green)]/30">
                    <div className="glow-dot"></div>
                    <span className="text-xs font-bold text-[var(--neon-green)] tracking-wider">LIVE</span>
                </div>
            </div>

            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                {tasks.length === 0 ? (
                    <div className="text-center py-16">
                        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                            <Cpu className="w-10 h-10 text-[var(--text-tertiary)]" />
                        </div>
                        <p className="text-[var(--text-secondary)] text-lg">No active tasks</p>
                        <p className="text-[var(--text-tertiary)] text-sm mt-1">AI agents standing by</p>
                    </div>
                ) : (
                    tasks.map((task, index) => {
                        const config = taskConfig[task.task_type] || { icon: Cpu, gradient: 'from-gray-500 to-gray-600', label: 'Processing' }
                        const IconComponent = config.icon

                        return (
                            <div
                                key={task.id}
                                className="group relative pl-6 animate-slide-up"
                                style={{ animationDelay: `${index * 0.08}s` }}
                            >
                                <div className={`absolute left-0 top-4 w-1.5 h-1.5 rounded-full ${
                                    task.status === 'processing' ? 'bg-[var(--neon-cyan)] shadow-[0_0_10px_var(--neon-cyan)]' :
                                    task.status === 'completed' ? 'bg-[var(--neon-green)]' : 'bg-[var(--text-tertiary)]'
                                }`}></div>
                                <div className={`absolute left-[2px] top-6 w-px h-[calc(100%-8px)] ${
                                    index === tasks.length - 1 ? 'bg-transparent' : 'bg-[var(--border-light)]'
                                }`}></div>

                                <div className="glass-card p-4 rounded-xl transition-all duration-300 hover:border-[var(--neon-purple)]/40">
                                    <div className="flex items-start gap-3">
                                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${config.gradient} flex items-center justify-center flex-shrink-0 shadow-lg`}>
                                            {task.status === 'processing' ? (
                                                <Loader2 className="w-5 h-5 text-white animate-spin" />
                                            ) : task.status === 'completed' ? (
                                                <CheckCircle2 className="w-5 h-5 text-white" />
                                            ) : (
                                                <IconComponent className="w-5 h-5 text-white" />
                                            )}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="font-semibold text-[var(--text-primary)] text-sm">
                                                    {config.label}
                                                </h3>
                                                <span className="font-mono text-[10px] text-[var(--text-tertiary)] bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded">
                                                    {task.id}
                                                </span>
                                            </div>

                                            <p className="text-xs text-[var(--text-secondary)] line-clamp-2 mb-2">
                                                {task.description}
                                            </p>

                                            {task.status === 'processing' && task.progress !== undefined ? (
                                                <div>
                                                    <div className="flex items-center justify-between text-[10px] mb-1.5">
                                                        <span className="text-[var(--text-tertiary)]">Processing</span>
                                                        <span className="font-bold text-[var(--neon-cyan)]">{task.progress}%</span>
                                                    </div>
                                                    <div className="progress-bar h-1.5">
                                                        <div
                                                            className="progress-fill"
                                                            style={{ width: `${task.progress}%` }}
                                                        />
                                                    </div>
                                                    {task.estimated_completion && (
                                                        <div className="flex items-center gap-1 mt-2 text-[10px] text-[var(--text-tertiary)]">
                                                            <Clock className="w-3 h-3" />
                                                            <span>ETA: {task.estimated_completion}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            ) : task.status === 'completed' ? (
                                                <div className="flex items-center gap-2">
                                                    <span className="badge badge-success text-[10px]">Completed</span>
                                                    {task.completed_at && (
                                                        <span className="text-[10px] text-[var(--text-tertiary)]">
                                                            {task.completed_at}
                                                        </span>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-1 text-[10px] text-[var(--text-tertiary)]">
                                                    <Clock className="w-3 h-3" />
                                                    <span>Queued</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )
                    })
                )}
            </div>
        </div>
    )
}
