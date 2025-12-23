'use client'

import { TrendingUp, TrendingDown, Briefcase, Activity, CheckCircle2, AlertCircle, Zap, Clock } from 'lucide-react'

interface StatCardProps {
    title: string
    value: string | number
    change?: number
    changeLabel?: string
    icon: React.ReactNode
    gradient: string
    delay?: number
}

function StatCard({ title, value, change, changeLabel, icon, gradient, delay = 0 }: StatCardProps) {
    const isPositive = change && change > 0
    const isNegative = change && change < 0

    return (
        <div
            className="stat-card group animate-slide-up"
            style={{ animationDelay: `${delay}s` }}
        >
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-5`}></div>
            </div>

            <div className="relative z-10 flex items-start justify-between">
                <div className="flex-1">
                    <p className="stat-label">{title}</p>
                    <p className="stat-value mt-2">{value}</p>
                    {change !== undefined && (
                        <div className={`stat-change ${isPositive ? 'positive' : isNegative ? 'negative' : ''}`}>
                            {isPositive ? (
                                <TrendingUp className="w-3.5 h-3.5" />
                            ) : isNegative ? (
                                <TrendingDown className="w-3.5 h-3.5" />
                            ) : null}
                            <span className="font-bold">{change > 0 ? '+' : ''}{change}</span>
                            {changeLabel && <span className="text-[var(--text-tertiary)] font-normal">{changeLabel}</span>}
                        </div>
                    )}
                </div>
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg transition-transform duration-200 group-hover:scale-105`}>
                    {icon}
                </div>
            </div>

            <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-b-xl`}></div>
        </div>
    )
}

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
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StatCard
                title="Total Matters"
                value={stats.totalMatters}
                change={5}
                changeLabel="this month"
                icon={<Briefcase className="w-7 h-7 text-[#0d1117]" />}
                gradient="from-[var(--gold-primary)] to-[var(--gold-dark)]"
                delay={0.05}
            />

            <StatCard
                title="Active Operations"
                value={stats.activeMatters}
                change={3}
                changeLabel="this week"
                icon={<Activity className="w-7 h-7 text-white" />}
                gradient="from-[var(--teal-primary)] to-[var(--teal-dark)]"
                delay={0.1}
            />

            <StatCard
                title="Urgent Deadlines"
                value={stats.urgentDeadlines}
                change={-1}
                changeLabel="from yesterday"
                icon={<AlertCircle className="w-7 h-7 text-white" />}
                gradient="from-[var(--rose)] to-[var(--amber)]"
                delay={0.15}
            />

            <StatCard
                title="AI Processing"
                value={stats.aiTasksProcessing}
                changeLabel="active now"
                icon={<Zap className="w-7 h-7 text-[#0d1117]" />}
                gradient="from-[var(--gold-light)] to-[var(--gold-primary)]"
                delay={0.2}
            />

            <StatCard
                title="Completed Today"
                value={stats.completedToday}
                change={3}
                changeLabel="vs yesterday"
                icon={<CheckCircle2 className="w-7 h-7 text-white" />}
                gradient="from-[var(--emerald)] to-[#059669]"
                delay={0.25}
            />

            <StatCard
                title="Overdue Items"
                value={stats.overdueItems}
                change={0}
                changeLabel="no change"
                icon={<Clock className="w-7 h-7 text-[#0d1117]" />}
                gradient="from-[var(--amber)] to-[#d97706]"
                delay={0.3}
            />
        </div>
    )
}