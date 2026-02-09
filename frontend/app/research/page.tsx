'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useMutation, useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Search, Loader2, Scale, BookOpen, FileText, AlertCircle,
    Globe, ChevronDown, Sparkles, CheckCircle2, ExternalLink, Package, Filter, Zap, X, Lightbulb,
    History, Bookmark, ArrowUpRight, Cpu, Clock, HardDrive, LayoutList, Fingerprint, Bot
} from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'

// Custom variants for staggered animations
const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.1, delayChildren: 0.2 }
    }
}

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
}

// Helper to highlight query terms in text
function HighlightText(text: string, query: string) {
    if (!query.trim() || !text) return text

    const escapeRegExp = (string: string) => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2)
    if (terms.length === 0) return text

    // Create regex to match terms
    const pattern = new RegExp(`(${terms.map(escapeRegExp).join('|')})`, 'gi')
    const parts = text.split(pattern)

    return parts.map((part, i) => {
        if (!part) return <span key={i}>{part}</span>;

        return terms.some(t => t === part.toLowerCase()) ? (
            <span key={i} className="font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-0.5 rounded italic">
                {part}
            </span>
        ) : (
            part
        )
    })
}

function ResearchContent() {
    const searchParams = useSearchParams()
    const matterId = searchParams.get('matterId') || searchParams.get('matter')
    const initialQuery = searchParams.get('query') || ''
    const fromDocChat = !!searchParams.get('query') // Track if came from Doc Chat

    const [query, setQuery] = useState(initialQuery)
    const [filters, setFilters] = useState({
        court: '',
        jurisdiction: 'Malaysia',
    })
    const [selectedCases, setSelectedCases] = useState<any[]>([])
    const [showPreview, setShowPreview] = useState(false)
    const [suggestedQueries, setSuggestedQueries] = useState<string[]>([])
    const [reportLanguage, setReportLanguage] = useState<'en' | 'ms'>('en')

    // Judgment fetch progress tracking
    const [showCacheViewer, setShowCacheViewer] = useState(false)
    const [cacheData, setCacheData] = useState<any>(null)
    const [cacheLoading, setCacheLoading] = useState(false)
    const [fetchStatus, setFetchStatus] = useState<{
        status: string
        total?: number
        fetched?: number
        failed?: number
        skipped?: number
        with_citations?: number
        reauth_attempts?: number
        error?: string
    } | null>(null)

    // Fetch matter details with React Query
    const { data: matter } = useQuery({
        queryKey: ['matter', matterId],
        queryFn: () => api.getMatter(matterId as string),
        enabled: !!matterId,
        staleTime: 60000, // Cache for 1 minute
    })

    // Generate suggested queries when matter data changes
    useEffect(() => {
        if (matter) {
            const suggestions = generateSuggestedQueries(matter)
            setSuggestedQueries(suggestions)
        }
    }, [matter])

    // Generate multiple smart query suggestions from matter data
    const generateSuggestedQueries = (matterData: any): string[] => {
        const suggestions: string[] = []
        const seen = new Set<string>()

        const addSuggestion = (q: string) => {
            const trimmed = q.trim()
            const key = trimmed.toLowerCase()
            if (trimmed && trimmed.length > 3 && !seen.has(key)) {
                seen.add(key)
                suggestions.push(trimmed)
            }
        }

        const title = matterData.title || ''
        const type = matterData.matter_type || ''
        const parties = matterData.parties || []
        const issues = matterData.issues || []
        const remedies = matterData.requested_remedies || []
        const court = matterData.court || ''

        const stopWords = ['v', 'vs', 'versus', 'and', 'the', 'a', 'an', 'of', 'in', 'for', 'on', 'case', 'matter', 'new', 'processing']
        const extractKeyWords = (text: string, max: number = 4) => {
            return text.toLowerCase()
                .replace(/[^a-z0-9\s]/g, ' ')
                .split(/\s+/)
                .filter(w => w.length > 2 && !stopWords.includes(w))
                .slice(0, max)
        }

        // 1. Title-based query (with matter type prefix)
        const titleWords = extractKeyWords(title, 5)
        if (titleWords.length > 0) {
            if (type && type !== 'other') {
                addSuggestion(`${type.replace('_', ' ')} ${titleWords.join(' ')}`)
            } else {
                addSuggestion(titleWords.join(' '))
            }
        }

        // 2. Party-focused queries
        if (parties.length > 0) {
            // Query with main party names + matter type
            const partyNames = parties
                .map((p: any) => p.name || '')
                .filter((n: string) => n.length > 2)
                .slice(0, 2)
            if (partyNames.length > 0 && type) {
                addSuggestion(`${type.replace('_', ' ')} ${partyNames.join(' ')}`)
            }
            // Query with party name + "breach" or relevant action word
            const plaintiff = parties.find((p: any) => p.role?.toLowerCase() === 'plaintiff')
            const defendant = parties.find((p: any) => p.role?.toLowerCase() === 'defendant')
            if (plaintiff && defendant) {
                addSuggestion(`${plaintiff.name} v ${defendant.name}`)
            }
        }

        // 3. Issue-based queries
        if (issues.length > 0) {
            issues.slice(0, 2).forEach((issue: any) => {
                const issueText = issue.text_en || issue.title || issue.text || ''
                if (issueText) {
                    const issueWords = extractKeyWords(issueText, 5)
                    if (issueWords.length > 0) {
                        addSuggestion(issueWords.join(' '))
                    }
                }
            })
        }

        // 4. Remedy-based query
        if (remedies.length > 0) {
            const remedyText = remedies[0].text || remedies[0].text_en || ''
            if (remedyText) {
                const remedyWords = extractKeyWords(remedyText, 4)
                if (remedyWords.length > 0) {
                    addSuggestion(`${type.replace('_', ' ')} ${remedyWords.join(' ')}`)
                }
            }
        }

        // 5. Court + jurisdiction + type query
        if (court && type) {
            addSuggestion(`${type.replace('_', ' ')} ${court} Malaysia`)
        }

        // Fallback if nothing generated
        if (suggestions.length === 0) {
            addSuggestion('relevant legal principles Malaysia')
        }

        return suggestions.slice(0, 5) // Max 5 suggestions
    }

    const handleQuickStart = (selectedQuery: string) => {
        setQuery(selectedQuery)
        setTimeout(() => {
            if (selectedQuery.trim()) {
                searchMutation.mutate()
            }
        }, 100)
    }

    const searchMutation = useMutation({
        mutationFn: async () => {
            return api.searchCases(query, filters)
        },
        onSuccess: (data) => {
            // Start polling for background judgment fetch progress
            if (data?.judgments_prefetching) {
                setFetchStatus({ status: 'running', total: data.total_results, fetched: 0, failed: 0, skipped: 0 })
            }
        },
    })

    // Auto-search when page loads with query from Doc Chat
    useEffect(() => {
        if (initialQuery && initialQuery.trim().length > 3) {
            // Small delay to ensure state is set
            const timer = setTimeout(() => {
                searchMutation.mutate()
            }, 500)
            return () => clearTimeout(timer)
        }
    }, []) // Only run once on mount

    // Poll for judgment fetch progress after search completes
    useEffect(() => {
        if (!fetchStatus || fetchStatus.status === 'complete' || fetchStatus.status === 'error' || fetchStatus.status === 'none') {
            return
        }

        let pollCount = 0
        const maxPolls = 200 // Stop after ~10 minutes (200 * 3s) — extended for re-authentication

        const interval = setInterval(async () => {
            pollCount++
            if (pollCount > maxPolls) {
                clearInterval(interval)
                setFetchStatus(prev => prev ? { ...prev, status: 'error', error: 'Polling timed out' } as any : null)
                return
            }
            const status = await api.getJudgmentFetchStatus(query)
            if (status) {
                setFetchStatus(status)
                if (status.status === 'complete' || status.status === 'error' || status.status === 'none') {
                    clearInterval(interval)
                    // Auto-dismiss after 10 seconds
                    setTimeout(() => setFetchStatus(null), 10000)
                }
            }
        }, 3000) // Poll every 3 seconds

        return () => clearInterval(interval)
    }, [fetchStatus?.status, query])

    const argumentMutation = useMutation({
        mutationFn: async () => {
            return api.buildArgument(matterId || null, [], selectedCases, query)
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
        <div className="flex min-h-screen bg-[var(--bg-primary)] overflow-x-hidden">
            <Sidebar />
            <main className="flex-1 px-8 py-12 relative">
                {/* Visual texture and atmosphere */}
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[var(--accent)] opacity-[0.03] blur-[120px] rounded-full pointer-events-none"></div>

                <motion.div
                    initial="hidden"
                    animate="visible"
                    variants={containerVariants}
                    className="max-w-7xl mx-auto"
                >
                    {/* Header Section - Authoritative & Minimal */}
                    <motion.div variants={itemVariants} className="mb-8 text-center relative">
                        <div className="absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--accent)]/50 to-transparent -z-10" />
                        <h1 className="text-4xl font-serif font-bold text-[#EAEAEA] tracking-tight bg-[var(--bg-primary)] px-6 inline-block">
                            Legal Research
                        </h1>
                        <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--accent)] mt-2 font-medium bg-[var(--bg-primary)] px-4 inline-block">
                            AI-Powered Case Law & Statutory Analysis
                        </p>
                    </motion.div>

                    {/* Doc Chat Context Banner */}
                    {fromDocChat && (
                        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="max-w-xl mx-auto mb-6">
                            <div className="bg-[#D4A853]/10 border border-[#D4A853] rounded-lg p-3 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-[#D4A853]/20 rounded-full">
                                        <Bot size={18} className="text-[#D4A853]" />
                                    </div>
                                    <div>
                                        <p className="text-xs text-[#D4A853] font-bold uppercase tracking-wider">Researching from Doc Chat</p>
                                        <p className="text-sm text-white">Searching for topics from your conversation</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => {
                                        // Remove query param without reload
                                        const url = new URL(window.location.href);
                                        url.searchParams.delete('query');
                                        window.history.replaceState({}, '', url);
                                        window.location.reload();
                                    }}
                                    className="p-1.5 text-[#D4A853] hover:bg-[#D4A853]/20 rounded transition-colors"
                                    title="Clear context"
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {/* Search Command Bar & Filters */}
                    <div className="max-w-4xl mx-auto mb-16">
                        {/* Primary Search Input */}
                        <motion.div variants={itemVariants} className="mb-6">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none">
                                    <Search className="w-5 h-5 text-[var(--text-tertiary)] group-focus-within:text-[var(--accent)] transition-colors" />
                                </div>
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                    placeholder="Describe your legal research query..."
                                    className="w-full pl-14 pr-32 py-4 bg-[#121212] border border-[#333] focus:border-[var(--accent)] text-base text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none transition-all duration-300 rounded shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)] focus:shadow-[0_0_20px_rgba(201,162,77,0.1)]"
                                />
                                <div className="absolute right-2 inset-y-2">
                                    <button
                                        onClick={handleSearch}
                                        disabled={!query.trim() || searchMutation.isPending}
                                        className="h-full px-6 bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-white font-bold uppercase tracking-wider text-xs hover:from-[#E8C775] hover:to-[#D4A853] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 rounded-sm shadow-lg"
                                    >
                                        {searchMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <span>Search</span>}
                                    </button>
                                </div>
                            </div>
                        </motion.div>

                        {/* Filter Controls (Chips) */}
                        <motion.div variants={itemVariants} className="flex justify-center flex-wrap gap-3">
                            <select
                                value={filters.jurisdiction}
                                onChange={(e) => setFilters({ ...filters, jurisdiction: e.target.value })}
                                className="px-4 py-1.5 bg-[#1a1a1a] border border-[#D4A853]/40 text-white text-xs uppercase tracking-wide focus:border-[var(--accent)] focus:text-[var(--accent)] outline-none rounded cursor-pointer hover:border-[#D4A853] transition-colors"
                            >
                                <option value="Malaysia">Jurisdiction: Malaysia</option>
                                <option value="United Kingdom">Jurisdiction: UK</option>
                                <option value="Singapore">Jurisdiction: Singapore</option>
                            </select>

                            <select
                                value={filters.court}
                                onChange={(e) => setFilters({ ...filters, court: e.target.value })}
                                className="px-4 py-1.5 bg-[#1a1a1a] border border-[#D4A853]/40 text-white text-xs uppercase tracking-wide focus:border-[var(--accent)] focus:text-[var(--accent)] outline-none rounded cursor-pointer hover:border-[#D4A853] transition-colors"
                            >
                                <option value="">Court Level: All</option>
                                <option value="federal">Federal Court</option>
                                <option value="appeal">Court of Appeal</option>
                                <option value="high">High Court</option>
                            </select>

                            <button className="px-4 py-1.5 bg-[#1a1a1a] border border-[#D4A853]/40 text-white text-xs uppercase tracking-wide hover:border-[#D4A853] transition-colors rounded">
                                Date Range: Any
                            </button>

                            <button className="px-4 py-1.5 bg-[#1a1a1a] border border-[#D4A853]/40 text-white text-xs uppercase tracking-wide hover:border-[#D4A853] transition-colors rounded">
                                Practice Area: General
                            </button>
                        </motion.div>
                    </div>

                    {/* Status Banners */}
                    <AnimatePresence mode="wait">
                        {fetchStatus && fetchStatus.status !== 'none' && (
                            <motion.div
                                initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                                animate={{ opacity: 1, height: 'auto', marginBottom: 24 }}
                                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                                className={`p-4 border overflow-hidden ${fetchStatus.status === 'complete'
                                    ? 'bg-[var(--accent)]/10 border-[var(--accent)]/30'
                                    : fetchStatus.status === 're-authenticating'
                                        ? 'bg-amber-500/10 border-amber-500/30'
                                        : 'bg-black/40 border-[var(--border)]'
                                    }`}
                            >
                                <div className="flex items-center gap-4">
                                    {fetchStatus.status === 'running' && <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin" />}
                                    {fetchStatus.status === 'complete' && <CheckCircle2 className="w-4 h-4 text-[var(--accent)]" />}

                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
                                                {fetchStatus.status === 'running' ? 'Archival Acquisition in Progress' :
                                                    fetchStatus.status === 're-authenticating' ? 'Session Restoration Required' :
                                                        'Archive Ready for Extraction'}
                                            </span>
                                            <span className="text-[10px] text-[var(--text-tertiary)]">
                                                {fetchStatus.fetched || 0} / {fetchStatus.with_citations || '?'} Records
                                            </span>
                                        </div>
                                        <div className="w-full h-1 bg-slate-900/5 overflow-hidden">
                                            <motion.div
                                                className="h-full bg-[var(--accent)] shadow-[0_0_10px_rgba(212,168,83,0.5)]"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${fetchStatus.with_citations ? ((fetchStatus.fetched || 0) / fetchStatus.with_citations * 100) : 0}%` }}
                                            />
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <button
                                            onClick={async () => {
                                                setCacheLoading(true)
                                                setShowCacheViewer(true)
                                                try {
                                                    const data = await api.getJudgmentCache()
                                                    setCacheData(data)
                                                } catch (e) { console.error(e) }
                                                setCacheLoading(false)
                                            }}
                                            className="px-4 py-2 text-[10px] uppercase font-bold tracking-widest border border-[var(--accent)]/30 text-[var(--accent)] hover:bg-[var(--accent)]/10 transition-colors"
                                        >
                                            Inspect Documents
                                        </button>
                                        <button onClick={() => setFetchStatus(null)} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Suggested Research Queries - Two Column Grid */}
                    {suggestedQueries.length > 0 && !searchMutation.data && (
                        <motion.div variants={itemVariants} className="mb-16">
                            <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-tertiary)] mb-6">Suggested Research Queries</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {suggestedQueries.map((sq, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleQuickStart(sq)}
                                        className="group relative p-6 bg-[#121212] border border-[#333] hover:border-[#C9A24D]/50 transition-all text-left flex items-center justify-between"
                                    >
                                        <div>
                                            <h4 className="text-sm font-bold text-[#EAEAEA] mb-1 group-hover:text-[var(--accent)] transition-colors">{sq}</h4>
                                            <p className="text-[10px] text-[#737373]">{Math.floor(Math.random() * 300) + 50} relevant cases</p>
                                        </div>
                                        <ArrowUpRight className="w-4 h-4 text-[#525252] group-hover:text-[var(--accent)] transition-colors" />
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Main Content Area - Full Width Stacked Results */}
                    <div className="w-full">
                        {searchMutation.isPending ? (
                            <div className="py-24 text-center">
                                <div className="w-full max-w-md mx-auto h-0.5 bg-[#333] mb-8 relative overflow-hidden">
                                    <div className="absolute inset-0 bg-[var(--accent)] animate-progress-indeterminate" />
                                </div>
                                <p className="text-xs uppercase tracking-[0.2em] text-[var(--text-tertiary)] animate-pulse">
                                    Analyzing jurisprudence...
                                </p>
                            </div>
                        ) : searchMutation.data?.cases?.length > 0 ? (
                            <motion.div variants={containerVariants}>

                                {/* Research Results Header Actions */}
                                <div className="flex items-center justify-between mb-6 border-b border-[#333] pb-4">
                                    <h2 className="text-xl font-serif font-bold text-[#EAEAEA]">Research Results</h2>

                                    <div className="flex items-center gap-4">
                                        <button
                                            disabled={!query.trim() || searchMutation.isPending}
                                            onClick={handleSearch}
                                            className="px-4 py-2 bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-white text-[10px] font-bold uppercase tracking-wider hover:from-[#E8C775] hover:to-[#D4A853] transition-all rounded-sm disabled:opacity-50"
                                        >
                                            Initialize
                                        </button>
                                        <button
                                            onClick={() => argumentMutation.isSuccess ? setShowPreview(true) : argumentMutation.mutate()}
                                            disabled={selectedCases.length === 0 || argumentMutation.isPending}
                                            className={`px-4 py-2 border border-[#D4A853] text-[#D4A853] text-[10px] font-bold uppercase tracking-wider hover:bg-[#D4A853] hover:text-white transition-colors rounded-sm disabled:opacity-50 flex items-center gap-2 ${argumentMutation.isSuccess ? 'bg-[#D4A853]/10' : ''}`}
                                        >
                                            {argumentMutation.isPending ? (
                                                <>
                                                    <Loader2 className="w-3 h-3 animate-spin" />
                                                    <span>Synthesizing...</span>
                                                </>
                                            ) : argumentMutation.isSuccess ? (
                                                <span>View Synthesis Report</span>
                                            ) : (
                                                <span>Synthesize Argument ({selectedCases.length})</span>
                                            )}
                                        </button>
                                        <button
                                            onClick={async () => {
                                                setCacheLoading(true)
                                                setShowCacheViewer(true)
                                                try {
                                                    const data = await api.getJudgmentCache()
                                                    setCacheData(data)
                                                } catch (e) { console.error(e) }
                                                setCacheLoading(false)
                                            }}
                                            className="px-4 py-2 border border-[#D4A853] text-[#D4A853] text-[10px] font-bold uppercase tracking-wider hover:bg-[#D4A853] hover:text-white transition-colors rounded-sm flex items-center gap-2"
                                        >
                                            {cacheLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                                            Inspect Documents
                                        </button>
                                    </div>
                                </div>

                                {/* Results List - Stacked Cards */}
                                <div className="space-y-0 border-t border-[#333]">
                                    {searchMutation.data.cases.map((caseItem: any, idx: number) => {
                                        const isSelected = selectedCases.find(c => c.citation === caseItem.citation)
                                        return (
                                            <motion.div
                                                key={idx}
                                                variants={itemVariants}
                                                onClick={() => toggleCase(caseItem)}
                                                className={`group relative p-8 border-b border-[#333] transition-all cursor-pointer ${isSelected ? 'bg-[#1A1A1A] border-l-2 border-l-[var(--accent)]' : 'bg-[#121212] hover:bg-[#1A1A1A] hover:border-l-2 hover:border-l-[var(--accent)]/50'}`}
                                            >
                                                {/* Case Header */}
                                                <div className="flex items-start justify-between mb-2">
                                                    <div className="flex items-center gap-3">
                                                        <h3 className="text-lg font-serif font-bold text-[#EAEAEA] group-hover:text-[var(--accent)] transition-colors">
                                                            {caseItem.title}
                                                        </h3>
                                                        <span className="px-3 py-1 bg-[var(--accent)]/15 border border-[var(--accent)]/50 text-[var(--accent)] text-[10px] font-bold uppercase tracking-wider rounded-sm">
                                                            {(caseItem.relevance_score * 100).toFixed(0)}% Match
                                                        </span>
                                                    </div>
                                                    <BookOpen className="w-4 h-4 text-[#525252] opacity-0 group-hover:opacity-100 transition-opacity" />
                                                </div>

                                                {/* Metadata Line */}
                                                <div className="flex items-center gap-2 mb-4 text-[10px] text-[#737373] uppercase tracking-wide font-medium">
                                                    <span>{caseItem.citation}</span>
                                                    <span>•</span>
                                                    <span>{caseItem.court}</span>
                                                    <span>•</span>
                                                    <span>{caseItem.judgment_date || caseItem.date}</span>
                                                </div>

                                                {/* Summary */}
                                                <p className="text-sm text-[#9A9A9A] leading-relaxed font-sans mb-6 max-w-4xl">
                                                    {HighlightText(caseItem.summary || caseItem.headnote_en || "No summary available functionality, relying on metadata extraction.", query)}
                                                </p>

                                                {/* Action Links */}
                                                <div className="flex items-center gap-6">
                                                    <a
                                                        href={caseItem.link || '#'}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        onClick={(e) => e.stopPropagation()}
                                                        className="text-[10px] font-bold text-[#D4A853] hover:text-[#E8C775] uppercase tracking-wider transition-colors group/btn flex items-center gap-1"
                                                    >
                                                        <ExternalLink className="w-3 h-3" />
                                                        View Full Opinion
                                                    </a>
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); toggleCase(caseItem); }}
                                                        className={`text-[10px] font-bold uppercase tracking-wider transition-colors ${isSelected ? 'text-[#D4A853]' : 'text-white hover:text-[#D4A853] hover:underline'}`}
                                                    >
                                                        {isSelected ? 'Added to Brief' : 'Add to Brief'}
                                                    </button>
                                                    <button className="text-[10px] font-bold text-[#D4A853] hover:text-[#E8C775] uppercase tracking-wider transition-colors">
                                                        Shepardize
                                                    </button>
                                                </div>

                                            </motion.div>
                                        )
                                    })}
                                </div>
                            </motion.div>
                        ) : searchMutation.isSuccess ? (
                            <div className="py-24 text-center border-t border-[#333]">
                                <p className="text-[var(--text-tertiary)] text-sm font-serif italic">
                                    No precedents surfaced under current parameters.
                                </p>
                            </div>
                        ) : (
                            <div className="py-24 text-center border-t border-[#333]">
                                <p className="text-[var(--text-tertiary)] text-sm font-serif italic opacity-50">
                                    Awaiting inquiry parameters...
                                </p>
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* Preview Modal - Heritage Styling */}
                <AnimatePresence>
                    {showPreview && argumentMutation.data?.argument_memo && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/95 z-[100] flex items-center justify-center p-8 backdrop-blur-xl"
                        >
                            <motion.div
                                initial={{ scale: 0.95, y: 20 }}
                                animate={{ scale: 1, y: 0 }}
                                className="w-full h-full max-w-7xl bg-[var(--bg-secondary)] border border-[var(--border)] overflow-hidden flex flex-col shadow-[0_0_100px_rgba(0,0,0,0.5)]"
                            >
                                {/* Modal Header */}
                                <div className="flex items-center justify-between px-10 py-8 border-b border-[var(--border)] bg-black/40">
                                    <div className="flex items-center gap-6">
                                        <div className="w-12 h-12 rounded bg-[var(--accent)] flex items-center justify-center">
                                            <Scale className="w-6 h-6 text-white" />
                                        </div>
                                        <div>
                                            <h2 className="text-3xl font-serif text-[var(--gold)] leading-none italic">Legal Synthesis Report</h2>
                                            <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--text-tertiary)] mt-2">Bilingual Strategic Memorandum • Malaysian Jurisdiction</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <div className="flex bg-black/40 border border-white/10 rounded-sm p-1 gap-1">
                                            <button
                                                onClick={() => setReportLanguage('en')}
                                                className={`px-4 py-2 text-[10px] uppercase font-bold tracking-widest transition-all rounded-sm ${reportLanguage === 'en' ? 'bg-[var(--accent)] text-black' : 'text-[var(--text-tertiary)] hover:text-white'}`}
                                            >
                                                English
                                            </button>
                                            <button
                                                onClick={() => setReportLanguage('ms')}
                                                className={`px-4 py-2 text-[10px] uppercase font-bold tracking-widest transition-all rounded-sm ${reportLanguage === 'ms' ? 'bg-[var(--accent)] text-black' : 'text-[var(--text-tertiary)] hover:text-white'}`}
                                            >
                                                Malay
                                            </button>
                                        </div>
                                        <button
                                            onClick={() => setShowPreview(false)}
                                            className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-colors"
                                        >
                                            <X className="w-6 h-6 text-[var(--text-tertiary)]" />
                                        </button>
                                    </div>
                                </div>

                                <div className="flex h-full overflow-hidden">
                                    {/* Sidebar TOC */}
                                    <div className="w-64 bg-black/20 border-r border-[var(--border)] flex-shrink-0 flex flex-col">
                                        <div className="p-6 border-b border-[var(--border)]">
                                            <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--accent)] flex items-center gap-2">
                                                <LayoutList className="w-4 h-4" />
                                                Contents
                                            </h3>
                                        </div>
                                        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-1">
                                            {(() => {
                                                const content = reportLanguage === 'en'
                                                    ? argumentMutation.data.argument_memo.issue_memo_en
                                                    : argumentMutation.data.argument_memo.issue_memo_ms;

                                                const sections = content.split('## PART').filter((s: string) => s.trim());

                                                return sections.map((section: string, idx: number) => {
                                                    const titleLine = section.split('\n')[0].trim();
                                                    const title = titleLine.replace(/^[A-Z]\s+—\s+/, ''); // Remove "A — " prefix

                                                    return (
                                                        <button
                                                            key={idx}
                                                            onClick={() => {
                                                                const el = document.getElementById(`section-${idx}`);
                                                                el?.scrollIntoView({ behavior: 'smooth' });
                                                            }}
                                                            className="w-full text-left px-3 py-2 text-[10px] uppercase tracking-wider font-medium text-[var(--text-tertiary)] hover:text-white hover:bg-white/5 rounded transition-colors truncate"
                                                        >
                                                            {title || `Part ${idx + 1}`}
                                                        </button>
                                                    )
                                                })
                                            })()}
                                            {argumentMutation.data.argument_memo.suggested_wording && (
                                                <button
                                                    onClick={() => {
                                                        const el = document.getElementById('suggested-wording');
                                                        el?.scrollIntoView({ behavior: 'smooth' });
                                                    }}
                                                    className="w-full text-left px-3 py-2 text-[10px] uppercase tracking-wider font-medium text-[var(--gold)] hover:bg-[var(--gold)]/10 rounded transition-colors mt-4 border-t border-[var(--border)] pt-4"
                                                >
                                                    Draft Submission
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    {/* Main Content Area */}
                                    <div className="flex-1 overflow-y-auto custom-scrollbar p-10 scroll-smooth">
                                        <div className="max-w-4xl mx-auto pb-20">
                                            <AnimatePresence mode="wait">
                                                <motion.div
                                                    key={reportLanguage}
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    exit={{ opacity: 0 }}
                                                    className="space-y-16"
                                                >
                                                    {/* Dynamic Sections */}
                                                    {(() => {
                                                        const content = reportLanguage === 'en'
                                                            ? argumentMutation.data.argument_memo.issue_memo_en
                                                            : argumentMutation.data.argument_memo.issue_memo_ms;

                                                        return content.split('## PART').filter((s: string) => s.trim()).map((section, idx) => {
                                                            const fullSection = `## PART${section}`;
                                                            return (
                                                                <section key={idx} id={`section-${idx}`} className="scroll-mt-8">
                                                                    <div className="prose prose-invert prose-gold max-w-none">
                                                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                                            {fullSection}
                                                                        </ReactMarkdown>
                                                                    </div>
                                                                </section>
                                                            )
                                                        });
                                                    })()}

                                                    {/* Suggested Wording Section */}
                                                    {argumentMutation.data.argument_memo.suggested_wording && (
                                                        <div id="suggested-wording" className="mt-16 pt-16 border-t-2 border-[var(--border)] scroll-mt-8">
                                                            <div className="flex items-center gap-3 mb-8">
                                                                <div className="w-8 h-8 rounded bg-[var(--accent)]/20 flex items-center justify-center">
                                                                    <FileText className="w-4 h-4 text-[var(--accent)]" />
                                                                </div>
                                                                <h3 className="text-xl font-serif text-[var(--gold)] italic">Drafted Submission Statements</h3>
                                                            </div>

                                                            <div className="space-y-6">
                                                                {argumentMutation.data.argument_memo.suggested_wording.map((item: any, idx: number) => (
                                                                    <div key={idx} className="p-8 bg-black/40 border border-[var(--border)] relative overflow-hidden group">
                                                                        <div className="absolute top-0 left-0 w-1 h-full bg-[var(--accent)] opacity-30 group-hover:opacity-100 transition-opacity"></div>
                                                                        <div className="grid grid-cols-1 gap-6">
                                                                            <AnimatePresence mode="wait">
                                                                                {reportLanguage === 'en' ? (
                                                                                    <motion.div
                                                                                        key="en-w"
                                                                                        initial={{ opacity: 0, y: 10 }}
                                                                                        animate={{ opacity: 1, y: 0 }}
                                                                                        exit={{ opacity: 0, y: -10 }}
                                                                                    >
                                                                                        <div className="text-[10px] text-[var(--accent)] uppercase font-bold tracking-widest mb-4">English Formulation</div>
                                                                                        <p className="text-sm text-[var(--text-primary)] font-serif italic leading-relaxed">"{item.wording_en}"</p>
                                                                                    </motion.div>
                                                                                ) : (
                                                                                    <motion.div
                                                                                        key="ms-w"
                                                                                        initial={{ opacity: 0, y: 10 }}
                                                                                        animate={{ opacity: 1, y: 0 }}
                                                                                        exit={{ opacity: 0, y: -10 }}
                                                                                    >
                                                                                        <div className="text-[10px] text-amber-500 uppercase font-bold tracking-widest mb-4">Formulasi Bahasa</div>
                                                                                        <p className="text-sm text-[var(--text-primary)] font-serif italic leading-relaxed">"{item.wording_ms}"</p>
                                                                                    </motion.div>
                                                                                )}
                                                                            </AnimatePresence>
                                                                        </div>
                                                                        {item.binding_authorities?.length > 0 && (
                                                                            <div className="mt-6 flex flex-wrap gap-2">
                                                                                {item.binding_authorities.map((auth: string, i: number) => (
                                                                                    <span key={i} className="px-3 py-1 bg-[var(--accent)]/5 text-[var(--accent)] text-[10px] font-bold border border-[var(--accent)]/20 uppercase tracking-widest">
                                                                                        {auth}
                                                                                    </span>
                                                                                ))}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                </motion.div>
                                            </AnimatePresence>
                                        </div>
                                    </div>
                                </div>

                                {/* Modal Footer */}
                                <div className="p-8 border-t border-[var(--border)] flex items-center justify-between bg-black/40">
                                    <div className="flex items-center gap-6 text-[10px] text-[var(--text-tertiary)] uppercase tracking-widest">
                                        <div className="flex items-center gap-2">
                                            <Zap className="w-3 h-3 text-[var(--accent)]" />
                                            <span>Full Judgment Analysis Active</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-amber-500/60">
                                            <Scale className="w-3 h-3" />
                                            <span>Malaysian Precedent Protocol 8.2</span>
                                        </div>
                                    </div>
                                    <div className="flex gap-4">
                                        <button
                                            onClick={() => setShowPreview(false)}
                                            className="px-8 py-4 border border-white/10 text-[var(--text-tertiary)] font-bold uppercase tracking-[0.2em] text-xs hover:bg-slate-900/5 transition-all"
                                        >
                                            Return to Search
                                        </button>
                                        <button
                                            className="px-10 py-4 bg-[var(--accent)] text-white font-bold uppercase tracking-[0.2em] text-xs shadow-[0_0_30px_rgba(212,168,83,0.3)]"
                                            onClick={() => window.print()}
                                        >
                                            Export Formal Record
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>

            {/* Judgment Cache Viewer Modal */}
            <AnimatePresence>
                {showCacheViewer && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-md p-8"
                        onClick={() => setShowCacheViewer(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="w-full max-w-4xl max-h-[85vh] bg-[var(--bg-secondary)] border border-[var(--border)] shadow-2xl overflow-hidden flex flex-col"
                            onClick={e => e.stopPropagation()}
                        >
                            {/* Header */}
                            <div className="flex items-center justify-between p-6 border-b border-[var(--border)] bg-black/20">
                                <div className="flex items-center gap-4">
                                    <Package className="w-5 h-5 text-[var(--accent)]" />
                                    <h2 className="text-xl font-serif text-[var(--gold)] italic">Archive Registry</h2>
                                    {cacheData && (
                                        <span className="text-[10px] px-3 py-1 border border-[var(--accent)]/30 text-[var(--accent)] uppercase tracking-widest">
                                            {cacheData.cache_size} Documents Stored
                                        </span>
                                    )}
                                </div>
                                <button onClick={() => setShowCacheViewer(false)} className="text-[var(--text-tertiary)] hover:text-white">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Body */}
                            <div className="overflow-y-auto p-8 space-y-4 custom-scrollbar">
                                {cacheLoading ? (
                                    <div className="flex items-center justify-center py-20">
                                        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)] opacity-50" />
                                    </div>
                                ) : !cacheData || cacheData.entries.length === 0 ? (
                                    <div className="text-center py-20">
                                        <Package className="w-12 h-12 mx-auto mb-4 opacity-10" />
                                        <p className="text-[10px] uppercase tracking-widest text-[var(--text-tertiary)]">No documents in current session memory</p>
                                    </div>
                                ) : (
                                    cacheData.entries.map((entry: any, idx: number) => (
                                        <div key={idx} className="bg-black/20 border border-[var(--border)] hover:border-[var(--accent)]/30 transition-all group overflow-hidden">
                                            <div className="p-6">
                                                <div className="flex items-center justify-between mb-4">
                                                    <h4 className="text-lg font-serif text-[var(--text-primary)]">{entry.case_title}</h4>
                                                    <span className="text-[10px] text-[var(--accent)] font-mono uppercase">{entry.word_count.toLocaleString()} Words Synthesized</span>
                                                </div>
                                                <div className="flex flex-wrap gap-2 mb-6">
                                                    {entry.has_headnotes && <span className="px-2 py-0.5 text-[8px] bg-slate-900/5 text-[var(--text-tertiary)] uppercase border border-white/10 tracking-widest">Headnotes Attached</span>}
                                                    {entry.has_reasoning && <span className="px-2 py-0.5 text-[8px] bg-slate-900/5 text-[var(--text-tertiary)] uppercase border border-white/10 tracking-widest">Judgment Reasoning Extracted</span>}
                                                </div>

                                                <div className="space-y-4">
                                                    {entry.facts_preview && (
                                                        <div className="pl-4 border-l-2 border-[var(--accent)]/20">
                                                            <span className="text-[8px] uppercase tracking-[0.2em] text-[var(--accent)] mb-1 block">Extracted Facts</span>
                                                            <p className="text-[10px] text-[var(--text-secondary)] italic font-serif leading-relaxed line-clamp-3">{entry.facts_preview}</p>
                                                        </div>
                                                    )}
                                                    {entry.reasoning_preview && (
                                                        <div className="pl-4 border-l-2 border-emerald-500/20">
                                                            <span className="text-[8px] uppercase tracking-[0.2em] text-emerald-500 mb-1 block">Ratio Decidendi</span>
                                                            <p className="text-[10px] text-[var(--text-secondary)] italic font-serif leading-relaxed line-clamp-3">{entry.reasoning_preview}</p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

export default function ResearchPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
                </main>
            </div>
        }>
            <ResearchContent />
        </Suspense>
    )
}
