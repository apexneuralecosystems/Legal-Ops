'use client'

import React from 'react'
import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { motion } from 'framer-motion'

interface Matter {
    id: string
    matter_id: string
    title: string
    status: string
    priority?: 'HIGH' | 'MEDIUM' | 'LOW'
    deadline?: string
}

interface MatterSummaryPanelProps {
    matters: Matter[]
}

export default function MatterSummaryPanel({ matters }: MatterSummaryPanelProps) {
    // Helper to format priority colors
    const getPriorityColor = (priority: string = 'MEDIUM') => {
        switch (priority) {
            case 'HIGH': return 'text-[#8B2E2E] bg-[#8B2E2E]/10 border-[#8B2E2E]/20';
            case 'MEDIUM': return 'text-[#C9A24D] bg-[#C9A24D]/10 border-[#C9A24D]/20';
            case 'LOW': return 'text-[#5F6B61] bg-[#5F6B61]/10 border-[#5F6B61]/20';
            default: return 'text-[#9A9A9A] bg-[#262626] border-transparent';
        }
    }

    return (
        <div className="bg-[#121212] border border-[#333] rounded-lg overflow-hidden flex flex-col h-full shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
            {/* Header */}
            <div className="px-8 py-6 border-b border-[#333] flex justify-between items-end">
                <div>
                    <h2 className="text-xl font-serif font-bold text-[#EAEAEA]">Matter Registry</h2>
                    <p className="text-[11px] text-[#9A9A9A] mt-1">Recent active cases</p>
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto">
                {matters.length === 0 ? (
                    <div className="p-8 text-center text-[#525252] text-sm italic">
                        No active matters found in registry.
                    </div>
                ) : (
                    <div className="divide-y divide-[#1A1A1A]">
                        {matters.map((matter, idx) => {
                            // Mocking priority for demo visualization as user requested specific look
                            const priorities = ['HIGH', 'MEDIUM', 'MEDIUM', 'HIGH', 'LOW'];
                            const priority = matter.priority || priorities[idx % priorities.length] as any;
                            const deadline = matter.deadline || `Feb ${10 + idx}, 2026`;

                            return (
                                <Link
                                    key={matter.matter_id || matter.id || `matter-${idx}`}
                                    href={`/matter/${matter.matter_id || matter.id}`}
                                    className="group flex items-center justify-between px-8 py-5 hover:bg-[#1A1A1A] transition-colors duration-200"
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-1.5">
                                            <span className="text-[10px] font-mono text-[#525252] group-hover:text-[#737373] transition-colors tabular-nums">
                                                {matter.matter_id || `MTR-2026-00${90 + idx}`}
                                            </span>
                                            <span className={`px-1.5 py-0.5 text-[9px] font-bold uppercase border rounded ${getPriorityColor(priority)}`}>
                                                {priority}
                                            </span>
                                        </div>
                                        <h3 className="text-sm font-medium text-[#EAEAEA] truncate pr-4 group-hover:text-white transition-colors">
                                            {matter.title}
                                        </h3>
                                        <div className="flex items-center gap-3 mt-1.5">
                                            <span className="text-[10px] uppercase font-bold text-[#9A9A9A]">{matter.status}</span>
                                            <span className="text-[10px] text-[#525252]">•</span>
                                            <span className="text-[10px] text-[#737373] font-mono tabular-nums">Deadline: {deadline}</span>
                                        </div>
                                    </div>

                                    <ChevronRight className="w-4 h-4 text-[#333] group-hover:text-[#C9A24D] transition-colors opacity-0 group-hover:opacity-100 transform group-hover:translate-x-1 duration-200" />
                                </Link>
                            )
                        })}
                    </div>
                )}
            </div>

        </div>
    )
}
