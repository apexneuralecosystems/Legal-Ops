'use client'

import { useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { Search, Loader2, BookOpen, Scale, Sparkles, Filter, Globe, Zap } from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'

function ResearchContent() {
    const searchParams = useSearchParams()
    const matterId = searchParams.get('matterId') || searchParams.get('matter')

    const [query, setQuery] = useState('')
    const [filters, setFilters] = useState({
        court: '',
        year: '',
        binding: '',
    })
    const [selectedCases, setSelectedCases] = useState<any[]>([])

    const searchMutation = useMutation({
        mutationFn: async () => {
            return api.searchCases(query, filters)
        },
    })

    const argumentMutation = useMutation({
        mutationFn: async () => {
            if (!matterId) throw new Error('No matter selected')
            return api.buildArgument(matterId, [], selectedCases)
        },
    })

    const handleSearch = () => {
        if (query.trim()) {
            searchMutation.mutate()
        }
    }

    const toggleCase = (caseItem: any) => {
        if (selectedCases.find(c => c.citation === caseItem.citation)) {
            setSelectedCases(selectedCases.filter(c => c.citation !== caseItem.citation))
        } else {
            setSelectedCases([...selectedCases, caseItem])
        }
    }

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />
            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-green)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--neon-cyan)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                <div className="mb-10 animate-fade-in">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="icon-box w-12 h-12">
                            <Search className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold gradient-text">Legal Research</h1>
                            <p className="text-[var(--text-secondary)] mt-1 flex items-center gap-2">
                                Search Malaysian caselaw with bilingual headnotes
                                <span className="px-2 py-0.5 bg-[var(--neon-green)]/10 text-[var(--neon-green)] text-xs rounded-full flex items-center gap-1">
                                    <Globe className="w-3 h-3" />
                                    Live CommonLII
                                </span>
                            </p>
                        </div>
                    </div>
                    <div className="cyber-line mt-6"></div>
                </div>

                {searchMutation.data?.live_data && (
                    <div className="mb-6 p-3 rounded-xl bg-[var(--neon-green)]/10 border border-[var(--neon-green)]/20 flex items-center gap-3 animate-slide-up">
                        <div className="w-2 h-2 bg-[var(--neon-green)] rounded-full animate-pulse"></div>
                        <span className="text-sm text-[var(--neon-green)] font-medium">Live Data from CommonLII</span>
                        <span className="text-[var(--text-tertiary)]">|</span>
                        <span className="text-sm text-[var(--text-secondary)]">Real Malaysian legal cases</span>
                    </div>
                )}

                <div className="grid lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
                    <div className="lg:col-span-1 space-y-6">
                        <div className="card p-6 animate-slide-up">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Search className="w-5 h-5 text-[var(--neon-cyan)]" />
                                Search Query
                            </h2>

                            <div className="space-y-4">
                                <div className="relative">
                                    <input
                                        type="text"
                                        value={query}
                                        onChange={(e) => setQuery(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                        placeholder="e.g., breach of contract"
                                        className="w-full pl-4 pr-4 py-3 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-[var(--neon-cyan)] focus:ring-1 focus:ring-[var(--neon-cyan)] transition-all"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)] mb-2">
                                        <Filter className="w-4 h-4" />
                                        Filters
                                    </div>

                                    <select
                                        value={filters.court}
                                        onChange={(e) => setFilters({ ...filters, court: e.target.value })}
                                        className="w-full px-4 py-3 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:border-[var(--neon-cyan)]"
                                    >
                                        <option value="">All Courts</option>
                                        <option value="federal">Federal Court</option>
                                        <option value="appeal">Court of Appeal</option>
                                        <option value="high">High Court</option>
                                    </select>

                                    <input
                                        type="number"
                                        value={filters.year}
                                        onChange={(e) => setFilters({ ...filters, year: e.target.value })}
                                        placeholder="Year (e.g., 2020)"
                                        className="w-full px-4 py-3 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-[var(--neon-cyan)]"
                                    />

                                    <select
                                        value={filters.binding}
                                        onChange={(e) => setFilters({ ...filters, binding: e.target.value })}
                                        className="w-full px-4 py-3 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] text-[var(--text-primary)] focus:border-[var(--neon-cyan)]"
                                    >
                                        <option value="">All Status</option>
                                        <option value="binding">Binding Only</option>
                                        <option value="persuasive">Persuasive</option>
                                    </select>
                                </div>

                                <button
                                    onClick={handleSearch}
                                    disabled={!query.trim() || searchMutation.isPending}
                                    className="w-full btn-primary py-3 flex items-center justify-center gap-2"
                                >
                                    {searchMutation.isPending ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Searching...
                                        </>
                                    ) : (
                                        <>
                                            <Search className="w-5 h-5" />
                                            Search Cases
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {selectedCases.length > 0 && (
                            <div className="card p-6 animate-slide-up stagger-1">
                                <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                    <BookOpen className="w-5 h-5 text-[var(--neon-purple)]" />
                                    Selected ({selectedCases.length})
                                </h2>
                                <button
                                    onClick={() => argumentMutation.mutate()}
                                    disabled={!matterId || argumentMutation.isPending}
                                    className="w-full px-6 py-3 bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-[var(--neon-purple)]/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {argumentMutation.isPending ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Building...
                                        </>
                                    ) : (
                                        <>
                                            <Scale className="w-5 h-5" />
                                            Build Argument
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="lg:col-span-2">
                        <div className="card p-6 animate-slide-up stagger-2">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-[var(--neon-cyan)]" />
                                    Search Results
                                </h2>
                                {searchMutation.data?.total_results > 0 && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <span className="text-[var(--text-secondary)]">
                                            {searchMutation.data.total_results} {searchMutation.data.total_results === 1 ? 'case' : 'cases'}
                                        </span>
                                        {searchMutation.data.live_data && (
                                            <span className="px-2 py-1 bg-[var(--neon-green)]/10 text-[var(--neon-green)] text-xs font-medium rounded-full flex items-center gap-1">
                                                <div className="w-1.5 h-1.5 bg-[var(--neon-green)] rounded-full"></div>
                                                Live
                                            </span>
                                        )}
                                    </div>
                                )}
                            </div>

                            {searchMutation.isPending ? (
                                <div className="flex items-center justify-center py-20">
                                    <div className="text-center">
                                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--neon-green)] to-[var(--neon-cyan)] flex items-center justify-center shadow-lg animate-pulse">
                                            <Zap className="w-8 h-8 text-white" />
                                        </div>
                                        <p className="text-[var(--text-secondary)]">Searching caselaw database...</p>
                                    </div>
                                </div>
                            ) : searchMutation.data?.cases ? (
                                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                                    {searchMutation.data.cases.map((caseItem: any, idx: number) => (
                                        <div
                                            key={idx}
                                            className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-300 ${selectedCases.find(c => c.citation === caseItem.citation)
                                                ? 'border-[var(--neon-green)] bg-[var(--neon-green)]/5'
                                                : 'border-[var(--border-primary)] hover:border-[var(--neon-cyan)]/50 bg-[var(--bg-tertiary)]'
                                                }`}
                                            onClick={() => toggleCase(caseItem)}
                                        >
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex-1">
                                                    <h3 className="font-semibold text-[var(--text-primary)]">{caseItem.title}</h3>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <p className="text-sm text-[var(--text-secondary)]">{caseItem.citation}</p>
                                                        {caseItem.url && (
                                                            <a
                                                                href={caseItem.url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                onClick={(e) => e.stopPropagation()}
                                                                className="text-xs text-[var(--neon-cyan)] hover:underline"
                                                            >
                                                                View on CommonLII
                                                            </a>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 flex-shrink-0">
                                                    {caseItem.binding && (
                                                        <span className="px-2 py-1 bg-[var(--neon-blue)]/10 text-[var(--neon-blue)] text-xs font-medium rounded-lg">
                                                            Binding
                                                        </span>
                                                    )}
                                                    <span className="px-2 py-1 bg-[var(--bg-secondary)] text-[var(--text-secondary)] text-xs font-medium rounded-lg">
                                                        {caseItem.court}
                                                    </span>
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <div className="p-3 rounded-lg bg-[var(--bg-secondary)]">
                                                    <div className="text-xs font-medium text-[var(--neon-cyan)] mb-1">English Headnote</div>
                                                    <p className="text-sm text-[var(--text-secondary)]">{caseItem.headnote_en}</p>
                                                </div>
                                                <div className="p-3 rounded-lg bg-[var(--bg-secondary)]">
                                                    <div className="text-xs font-medium text-[var(--neon-orange)] mb-1">Malay Headnote</div>
                                                    <p className="text-sm text-[var(--text-secondary)]">{caseItem.headnote_ms}</p>
                                                </div>
                                            </div>

                                            <div className="mt-3 flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                                                <BookOpen className="w-4 h-4" />
                                                <span>Relevance: {(caseItem.relevance_score * 100).toFixed(0)}%</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-20">
                                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                                        <Search className="w-10 h-10 text-[var(--text-tertiary)]" />
                                    </div>
                                    <p className="text-[var(--text-secondary)]">Enter a search query to find relevant cases</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default function ResearchPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-[var(--neon-cyan)]" />
                </main>
            </div>
        }>
            <ResearchContent />
        </Suspense>
    )
}
