'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, Clock, User, FolderOpen, Plus, ChevronRight, FileText } from 'lucide-react'

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

const statusConfig: Record<string, { label: string; dotColor: string }> = {
    'intake': { label: 'Processing', dotColor: 'bg-blue-400' },
    'structured': { label: 'Review', dotColor: 'bg-amber-400' },
    'drafting': { label: 'Active', dotColor: 'bg-[#D4A853]' },
    'ready': { label: 'Ready', dotColor: 'bg-green-400' },
    'urgent': { label: 'Urgent', dotColor: 'bg-red-400' },
    'critical': { label: 'Critical', dotColor: 'bg-red-500' }
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
        if (diffMins < 60) return `${diffMins}m ago`
        if (diffHours < 24) return `${diffHours}h ago`
        return `${diffDays}d ago`
    }

    return (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            {/* Header */}
            <div className="p-5 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[var(--gold-primary)] flex items-center justify-center">
                        <FolderOpen className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-black">Active Matters</h2>
                        <p className="text-xs text-gray-500">{matters.length} cases in pipeline</p>
                    </div>
                </div>
                <Link
                    href="/upload"
                    className="flex items-center gap-2 px-4 py-2 bg-[var(--gold-primary)] hover:bg-[var(--gold-light)] text-white rounded-lg font-semibold text-sm transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    New Matter
                </Link>
            </div>

            {/* Search & Filter */}
            <div className="p-4 border-b border-gray-200 flex gap-3">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search matters..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg text-sm text-black placeholder-gray-400 focus:outline-none focus:border-[#D4A853] focus:bg-white"
                    />
                </div>
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:border-[#D4A853] focus:bg-white min-w-[140px]"
                >
                    <option>All Status</option>
                    <option>Urgent</option>
                    <option>Active</option>
                    <option>Review</option>
                    <option>Ready</option>
                </select>
            </div>

            {/* Matter List */}
            <div className="max-h-[360px] overflow-y-auto">
                {filteredMatters.length === 0 ? (
                    <div className="p-12 text-center">
                        <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center">
                            <FolderOpen className="w-8 h-8 text-[#D4A853]" />
                        </div>
                        <p className="text-gray-500">No matters found</p>
                        <p className="text-xs text-gray-400 mt-1">Try adjusting your filters</p>
                    </div>
                ) : (
                    <div className="divide-y divide-gray-200">
                        {filteredMatters.map((matter) => {
                            const matterStatus = getMatterStatus(matter)
                            const statusInfo = statusConfig[matterStatus] || { label: 'Unknown', dotColor: 'bg-gray-500' }
                            const matterId = matter.matter_id || matter.id || ''

                            return (
                                <Link
                                    key={matterId}
                                    href={`/matter/${matterId}`}
                                    className="group flex items-center gap-4 p-4 hover:bg-white/[0.02] transition-colors"
                                >
                                    <div className="w-10 h-10 rounded-lg bg-gray-100 border border-gray-200 flex items-center justify-center flex-shrink-0">
                                        <FileText className="w-5 h-5 text-[#D4A853]" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-mono text-[10px] text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                                                {matterId}
                                            </span>
                                            <div className="flex items-center gap-1.5">
                                                <div className={`w-1.5 h-1.5 rounded-full ${statusInfo.dotColor}`}></div>
                                                <span className="text-[10px] text-gray-400">{statusInfo.label}</span>
                                            </div>
                                        </div>
                                        <h3 className="text-sm font-medium text-black truncate group-hover:text-[#D4A853] transition-colors">
                                            {matter.title}
                                        </h3>
                                        <p className="text-xs text-gray-500 capitalize">
                                            {matter.matter_type?.replace('_', ' ') || 'General'} • {formatTimeAgo(matter.created_at)}
                                        </p>
                                    </div>
                                    <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-[#D4A853] group-hover:translate-x-1 transition-all" />
                                </Link>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}