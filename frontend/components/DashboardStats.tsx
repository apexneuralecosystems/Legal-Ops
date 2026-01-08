'use client'

import { TrendingUp, TrendingDown, Briefcase, Activity, CheckCircle2, AlertCircle, Zap, Clock } from 'lucide-react'

interface DashboardStatsProps {
    stats: {
        totalMatters: number
        activeMatters: number
        urgentDeadlines: number
        aiTasksProcessing: number
        completedToday: number
        overdueItems: number
    }
}

export default function DashboardStats({ stats }: DashboardStatsProps) {
    const cards = [
        {
            title: 'Total Matters',
            value: stats.totalMatters,
            change: null,
            changeLabel: '',
            icon: Briefcase,
            accent: true
        },
        {
            title: 'Active Operations',
            value: stats.activeMatters,
            change: null,
            changeLabel: '',
            icon: Activity,
            accent: false
        },
        {
            title: 'Urgent Deadlines',
            value: stats.urgentDeadlines,
            change: null,
            changeLabel: '',
            icon: AlertCircle,
            accent: false
        },
        {
            title: 'AI Processing',
            value: stats.aiTasksProcessing,
            change: null,
            changeLabel: '',
            icon: Zap,
            accent: true
        },
        {
            title: 'Completed Today',
            value: stats.completedToday,
            change: null,
            changeLabel: '',
            icon: CheckCircle2,
            accent: false
        },
        {
            title: 'Overdue Items',
            value: stats.overdueItems,
            change: null,
            changeLabel: '',
            icon: Clock,
            accent: false
        }
    ]

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {cards.map((card) => {
                const Icon = card.icon
                const isPositive = card.change && card.change > 0
                const isNegative = card.change && card.change < 0

                return (
                    <div
                        key={card.title}
                        className="bg-white border border-gray-200 rounded-xl p-4 hover:border-[#D4A853]/50 hover:shadow-lg transition-all group"
                    >
                        <div className="flex items-center justify-between mb-3">
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-[var(--gold-primary)]`}>
                                <Icon className="w-5 h-5 text-white" />
                            </div>
                        </div>
                        <p className="text-2xl font-bold text-black mb-1">{card.value}</p>
                        <p className="text-xs text-gray-500 mb-2">{card.title}</p>
                        {card.change !== null && (
                            <div className={`flex items-center gap-1 text-xs ${isPositive ? 'text-[#D4A853]' : isNegative ? 'text-gray-400' : 'text-gray-600'}`}>
                                {isPositive ? <TrendingUp className="w-3 h-3" /> : isNegative ? <TrendingDown className="w-3 h-3" /> : null}
                                <span>{card.change > 0 ? '+' : ''}{card.change}</span>
                                <span className="text-gray-600">{card.changeLabel}</span>
                            </div>
                        )}
                    </div>
                )
            })}
        </div>
    )
}