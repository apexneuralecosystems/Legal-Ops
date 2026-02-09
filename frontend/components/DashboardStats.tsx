'use client'

import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { motion } from 'framer-motion'

export interface StatCardItem {
    label: string
    value: string | number
    icon: LucideIcon
    trend?: string
    trendUp?: boolean | null // true=up, false=down, null=neutral
    color?: string
}

interface DashboardStatsProps {
    items: StatCardItem[]
}

export default function DashboardStats({ items }: DashboardStatsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {items.map((card, index) => (
                <motion.div
                    key={card.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="group relative p-6 bg-gradient-to-br from-[#121212] to-[#1A1A1A] border border-[#333] hover:border-[#C9A24D]/30 rounded-lg transition-all duration-300"
                >
                    {/* Hover Glow */}
                    <div className="absolute inset-0 bg-[#C9A24D]/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg" />

                    <div className="relative flex justify-between items-start mb-4">
                        <h3 className="text-[10px] font-bold text-[#9A9A9A] uppercase tracking-[0.2em]">
                            {card.label}
                        </h3>
                        <card.icon className="w-4 h-4 text-[#525252] group-hover:text-[#C9A24D] transition-colors" />
                    </div>

                    <div className="relative flex items-center justify-between">
                        <div className={`text-3xl font-sans font-semibold ${card.color || 'text-[#EAEAEA]'} tracking-tight tabular-nums`}>
                            {card.value}
                        </div>

                        {card.trend && (
                            <div className={`flex items-center gap-1 text-[10px] font-medium ${card.trendUp === true ? 'text-emerald-500' : card.trendUp === false ? 'text-[#C9A24D]' : 'text-[#737373]'}`}>
                                {card.trend}
                                {card.trendUp === true && <TrendingUp className="w-3 h-3" />}
                                {card.trendUp === false && <TrendingDown className="w-3 h-3" />}
                                {card.trendUp === null && <Minus className="w-3 h-3" />}
                            </div>
                        )}
                    </div>
                </motion.div>
            ))}
        </div>
    )
}
