'use client'

import { useState, useEffect } from 'react'
import { Bot, FileText, Search, Database, Cpu, Activity, CheckCircle2, Clock } from 'lucide-react'
import { motion } from 'framer-motion'

export interface AgentResource {
    id: string
    name: string
    role: string
    status: 'ACTIVE' | 'IDLE' | 'LEARNING'
    currentTask?: string
    efficiency: number
    history?: number[] // Array of past efficiency values for sparkline
    icon: any
}

interface ResourceGridProps {
    agents: AgentResource[]
}

export default function ResourceGrid({ agents }: ResourceGridProps) {

    return (
        <div className="bg-[#121212] border border-[#333] rounded-lg shadow-lg flex flex-col h-full min-h-[400px] overflow-hidden group hover:border-[#C9A24D]/30 transition-all duration-300">

            {/* Header */}
            <div className="px-6 py-4 border-b border-[#333] bg-[#141414] flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <Cpu className="w-4 h-4 text-[#C9A24D]" />
                    <div>
                        <h2 className="text-sm font-serif font-bold text-[#EAEAEA] tracking-wide">AI Resources</h2>
                        <span className="text-[9px] text-[#525252] font-mono uppercase tracking-[0.2em] block mt-0.5">Agent Allocation</span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[9px] font-bold text-[#737373]">OPTIMAL</span>
                    <Activity className="w-3 h-3 text-emerald-500" />
                </div>
            </div>

            {/* Grid Content */}
            <div className="flex-1 p-6 grid grid-cols-1 gap-4 overflow-y-auto custom-scrollbar bg-[#0B0B0B]">
                {agents.map((resource) => (
                    <div
                        key={resource.id}
                        className="bg-[#1A1A1A] border border-[#262626] rounded-md p-4 relative overflow-hidden group/card hover:border-[#C9A24D]/30 transition-all"
                    >
                        {/* Active Indicator Line */}
                        {resource.status === 'ACTIVE' && (
                            <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#C9A24D] shadow-[0_0_10px_rgba(201,162,77,0.5)]" />
                        )}

                        <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded bg-[#121212] border border-[#333] ${resource.status === 'ACTIVE' ? 'text-[#C9A24D]' : 'text-[#525252]'}`}>
                                    <resource.icon className="w-4 h-4" />
                                </div>
                                <div>
                                    <h4 className="text-xs font-bold text-[#EAEAEA]">{resource.name}</h4>
                                    <p className="text-[9px] text-[#737373] uppercase tracking-wider">{resource.role}</p>
                                </div>
                            </div>
                            <div className={`px-2 py-0.5 rounded text-[9px] font-bold border ${resource.status === 'ACTIVE'
                                ? 'bg-[#C9A24D]/10 text-[#C9A24D] border-[#C9A24D]/20'
                                : resource.status === 'IDLE'
                                    ? 'bg-[#262626] text-[#525252] border-[#333]'
                                    : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                                }`}>
                                {resource.status}
                            </div>
                        </div>

                        {/* Task / Context */}
                        <div className="mb-3 h-8">
                            {resource.currentTask ? (
                                <div className="flex items-start gap-2">
                                    <Activity className="w-3 h-3 text-[#C9A24D] mt-0.5 animate-pulse" />
                                    <span className="text-[10px] text-[#EAEAEA] leading-tight font-mono tabular-nums">{resource.currentTask}</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2">
                                    <CheckCircle2 className="w-3 h-3 text-[#525252]" />
                                    <span className="text-[10px] text-[#525252] italic">Ready for assignment</span>
                                </div>
                            )}
                        </div>

                        {/* Efficiency Bar & History */}
                        <div className="mt-auto">
                            <div className="flex items-end justify-between mb-2 h-8 gap-1">
                                {resource.history?.map((val, idx) => (
                                    <div
                                        key={idx}
                                        className={`w-1 rounded-t-sm transition-all duration-500 ${resource.status === 'ACTIVE' ? 'bg-[#C9A24D]/40 group-hover:bg-[#C9A24D]' : 'bg-[#333]'}`}
                                        style={{ height: `${val}%` }}
                                    />
                                )) || (
                                        // Fallback if no history
                                        <div className="w-full h-8 flex items-end gap-1">
                                            {[40, 60, 45, 70, 50, 65, 80, resource.efficiency].map((val, i) => (
                                                <div
                                                    key={i}
                                                    className={`w-1 rounded-t-sm bg-[#262626] ${i === 7 ? (resource.status === 'ACTIVE' ? 'bg-[#C9A24D]' : 'bg-[#525252]') : ''}`}
                                                    style={{ height: `${val}%` }}
                                                />
                                            ))}
                                        </div>
                                    )}
                            </div>

                            <div className="flex items-center gap-2">
                                <div className="flex-1 h-0.5 bg-[#121212] mb-0.5">
                                    <motion.div
                                        className={`h-full ${resource.status === 'ACTIVE' ? 'bg-[#C9A24D]' : 'bg-[#333]'}`}
                                        initial={{ width: 0 }}
                                        animate={{ width: `${resource.efficiency}%` }}
                                        transition={{ duration: 1 }}
                                    />
                                </div>
                                <span className="text-[9px] font-mono text-[#525252] tabular-nums">{Math.round(resource.efficiency)}% EFF</span>
                            </div>
                        </div>

                    </div>
                ))}
            </div>

            {/* Footer Stats */}
            <div className="px-4 py-3 bg-[#141414] border-t border-[#333] flex justify-between items-center text-[9px] text-[#737373]">
                <span className="tabular-nums">Total Load: 42%</span>
                <span className="flex items-center gap-1 tabular-nums">
                    <Clock className="w-3 h-3" />
                    Uptime: 99.9%
                </span>
            </div>
        </div>
    )
}
