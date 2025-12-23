'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, Clock, User, FolderOpen, Plus, ArrowUpRight, Sparkles } from 'lucide-react'

interface Matter {
    matter_id: string
    id?: string
    title: string
    matter_type?: string
    status: string
    created_at: string
    human_review_required: boolean
    time_remaining?: string
    assignee?: string
}

interface MatterSummaryPanelProps {
    matters: Matter[]
}

const statusConfig: Record<string, { label: string; className: string; gradient: string }> = {
    'intake': { label: 'Processing', className: 'badge-active', gradient: 'from-[var(--teal-primary)] to-[var(--teal-dark)]' },
    'structured': { label: 'Review', className: 'badge-pending', gradient: 'from-[var(--gold-primary)] to-[var(--gold-dark)]' },
    'drafting': { label: 'Active', className: 'badge-active', gradient: 'from-[var(--teal-primary)] to-[var(--emerald)]' },
    'ready': { label: 'Ready', className: 'badge-success', gradient: 'from-[var(--emerald)] to-[#059669]' },
    'urgent': { label: 'Urgent', className: 'badge-urgent', gradient: 'from-[var(--rose)] to-[var(--amber)]' },
    'critical': { label: 'Critical', className: 'badge-urgent', gradient: 'from-[var(--rose)] to-[#e11d48]' }
}

export default function MatterSummaryPanel({ matters }: MatterSummaryPanelProps) {
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState('All Status')

    const getMatterStatus = (matter: Matter) => {
        if (matter.human_review_required) return 'urgent'
        return matter.status
    }

    const filteredMatters = matters.filter(matter => {
        const matterId = matter.matter_id || matter.id || ''
        const matchesSearch = matter.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            matterId.toLowerCase().includes(searchQuery.toLowerCase())
        const matterStatus = getMatterStatus(matter)
        const matchesStatus = statusFilter === 'All Status' ||
            statusConfig[matterStatus]?.label === statusFilter
        return matchesSearch && matchesStatus
    })

    const formatTimeAgo = (dateString: string) => {
        const date = new Date(dateString)
        const now = new Date()
        const diffMs = now.getTime() - date.getTime()
        const diffMins = Math.floor(diffMs / 60000)
        const diffHours = Math.floor(diffMins / 60)
        const diffDays = Math.floor(diffHours / 24)

        if (diffMins < 60) return `${diffMins}m`
        if (diffHours < 24) return `${diffHours}h`
        return `${diffDays}d`
    }

    return (
        <div className="card p-6">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--gold-primary)] to-[var(--gold-dark)] flex items-center justify-center shadow-lg">
                        <FolderOpen className="w-6 h-6 text-[#0d1117]" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-[var(--text-primary)]">Active Matters</h2>
                        <p className="text-sm text-[var(--text-secondary)]">
                            <span className="text-[var(--teal-primary)]">{matters.length}</span> cases in pipeline
                        </p>
                    </div>
                </div>
                <Link
                    href="/upload"
                    className="btn-primary flex items-center gap-2 px-5 py-3 text-sm"
                >
                    <Plus className="w-4 h-4" />
                    New Matter
                </Link>
            </div>

            <div className="flex gap-4 mb-6">
                <div className="flex-1 relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)] group-focus-within:text-[var(--gold-primary)] transition-colors" />
                    <input
                        type="text"
                        placeholder="Search matters..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 rounded-xl text-sm"
                    />
                </div>
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-5 py-3 rounded-xl text-sm min-w-[160px]"
                >
                    <option>All Status</option>
                    <option>Urgent</option>
                    <option>Active</option>
                    <option>Review</option>
                    <option>Ready</option>
                </select>
            </div>

            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                {filteredMatters.length === 0 ? (
                    <div className="text-center py-16">
                        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                            <Sparkles className="w-10 h-10 text-[var(--text-tertiary)]" />
                        </div>
                        <p className="text-[var(--text-secondary)] text-lg">No matters found</p>
                        <p className="text-[var(--text-tertiary)] text-sm mt-1">Try adjusting your filters</p>
                    </div>
                ) : (
                    filteredMatters.map((matter, index) => {
                        const matterStatus = getMatterStatus(matter)
                        const statusInfo = statusConfig[matterStatus] || { label: 'Unknown', className: 'badge', gradient: 'from-gray-500 to-gray-600' }
                        const matterId = matter.matter_id || matter.id || ''

                        return (
                            <Link
                                key={matterId}
                                href={`/matter/${matterId}`}
                                className="group block matter-card animate-slide-up"
                                style={{ animationDelay: `${index * 0.05}s` }}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-2">
                                            <span className="font-mono text-xs text-[var(--teal-primary)] bg-[var(--bg-tertiary)] px-2 py-1 rounded-md">
                                                {matterId}
                                            </span>
                                            <span className={`badge ${statusInfo.className}`}>
                                                {statusInfo.label}
                                            </span>
                                        </div>
                                        <h3 className="font-semibold text-[var(--text-primary)] text-lg truncate group-hover:text-[var(--gold-primary)] transition-colors">
                                            {matter.title}
                                        </h3>
                                        <p className="text-sm text-[var(--text-tertiary)] capitalize mt-1">
                                            {matter.matter_type?.replace('_', ' ') || 'General Matter'}
                                        </p>
                                    </div>
                                    <ArrowUpRight className="w-5 h-5 text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100 group-hover:text-[var(--gold-primary)] transition-all transform group-hover:translate-x-1 group-hover:-translate-y-1" />
                                </div>

                                <div className="flex items-center gap-4 text-xs text-[var(--text-tertiary)] pt-3 border-t border-[var(--border-light)]">
                                    {matter.time_remaining && (
                                        <div className="flex items-center gap-1.5">
                                            <Clock className="w-3.5 h-3.5" />
                                            <span>{matter.time_remaining}</span>
                                        </div>
                                    )}
                                    {matter.assignee && (
                                        <div className="flex items-center gap-1.5">
                                            <User className="w-3.5 h-3.5" />
                                            <span>{matter.assignee}</span>
                                        </div>
                                    )}
                                    <span className="ml-auto font-mono">{formatTimeAgo(matter.created_at)} ago</span>
                                </div>
                            </Link>
                        )
                    })
                )}
            </div>
        </div>
    )
}