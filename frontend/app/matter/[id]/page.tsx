'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { ArrowLeft, FileText, Calendar, Users, AlertCircle, CheckCircle2, Download, Trash2, Target, AlertTriangle, Zap, Lightbulb, Loader2, Sparkles, Shield, Scale, Search, Package, MessageSquare, Bot, X } from 'lucide-react'
import Link from 'next/link'
import ParalegalChat from '@/components/ParalegalChat'
import { motion, AnimatePresence } from 'framer-motion'

import { api } from '@/lib/api'

export default function MatterDetailPage() {
    const params = useParams()
    const router = useRouter()
    const matterId = params.id as string
    const [showParalegalChat, setShowParalegalChat] = useState(false)

    const [matter, setMatter] = useState<any>(null)
    const [documents, setDocuments] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [caseStrength, setCaseStrength] = useState<any>(null)
    const [analyzingStrength, setAnalyzingStrength] = useState(false)

    useEffect(() => {
        if (matterId === 'undefined') {
            router.push('/dashboard')
            return
        }
        if (matterId) {
            loadData()
        }
    }, [matterId])

    const loadData = async () => {
        try {
            setLoading(true)
            const [matterData, documentsData] = await Promise.all([
                api.getMatter(matterId),
                api.getMatterDocuments(matterId)
            ])
            setMatter(matterData)
            setDocuments(documentsData)
        } catch (error) {
            console.error('Failed to load matter data:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async () => {
        if (window.confirm(`Are you sure you want to delete this matter?\n\nThis will permanently remove:\n• All documents\n• All pleadings\n• All translations\n\nThis action cannot be undone.`)) {
            try {
                await api.deleteMatter(matterId)
                alert('Matter deleted successfully')
                router.push('/dashboard')
            } catch (error: any) {
                console.error('Failed to delete matter:', error)
                alert(`Failed to delete matter: ${error.message || 'Unknown error'}`)
            }
        }
    }

    const analyzeCaseStrength = async () => {
        try {
            setAnalyzingStrength(true)
            const result = await api.analyzeCaseStrength(matterId)
            setCaseStrength(result.analysis)
        } catch (error: any) {
            console.error('Failed to analyze case strength:', error)
            alert(`Analysis failed: ${error.message || 'Unknown error'}`)
        } finally {
            setAnalyzingStrength(false)
        }
    }

    if (loading) {
        return (
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <div className="text-center">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--accent-bronze)] to-[var(--accent-gold)] flex items-center justify-center shadow-lg animate-pulse">
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <p className="text-[var(--text-secondary)]">Loading matter details...</p>
                    </div>
                </main>
            </div>
        )
    }

    if (!matter) {
        return (
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <div className="glass-card p-12 text-center max-w-md">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#ef4444]/10 flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-[#ef4444]" />
                        </div>
                        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Matter not found</h2>
                        <p className="text-[var(--text-secondary)] mb-6">The matter you're looking for doesn't exist.</p>
                        <Link href="/dashboard" className="inline-flex items-center gap-2 px-6 py-3 bg-black hover:bg-gray-900 text-[var(--gold-primary)] font-bold rounded-lg transition-colors shadow-lg border-2 border-[var(--gold-primary)]">
                            Back to Dashboard
                        </Link>
                    </div>
                </main>
            </div>
        )
    }

    const riskScores = matter.risk_scores || {}

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />

            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--accent-bronze)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--accent-gold)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--accent-gold)] mb-6 transition-colors animate-fade-in"
                >
                    <ArrowLeft className="w-5 h-5" />
                    <span className="font-medium">Back</span>
                </button>

                <div className="mb-8 animate-slide-up">
                    <div className="flex items-start justify-between mb-4 flex-wrap gap-4">
                        <div>
                            <div className="flex items-center gap-3 mb-2 flex-wrap">
                                <h1 className="text-3xl font-bold text-[var(--text-primary)]">{matter.title}</h1>
                                {matter.human_review_required && (
                                    <span className="px-3 py-1 bg-[var(--accent-gold)]/10 text-[var(--accent-gold)] text-xs font-semibold rounded-full border border-[var(--accent-gold)]/20">
                                        Requires Review
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)] flex-wrap">
                                <span className="font-mono px-2 py-1 bg-[var(--bg-tertiary)] rounded">{matter.matter_id}</span>
                                <span className="capitalize">{matter.matter_type?.replace('_', ' ')}</span>
                                <span className="px-2 py-1 bg-[var(--accent-gold)]/10 text-[var(--accent-gold)] rounded capitalize">{matter.status}</span>
                            </div>
                        </div>
                        <div className="flex gap-3 flex-wrap">
                            <Link
                                href={`/drafting?matterId=${matterId}`}
                                className="px-5 py-2.5 flex items-center gap-2 text-sm bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] text-[var(--accent-gold)] font-bold rounded-lg transition-colors shadow-lg border-2 border-[var(--accent-gold)]"
                            >
                                <Scale className="w-4 h-4" />
                                Drafting
                            </Link>
                            <button
                                onClick={() => setShowParalegalChat(true)}
                                className="px-5 py-2.5 bg-[var(--accent-gold)] hover:bg-[#B08D3C] text-black font-bold rounded-lg transition-colors shadow-lg shadow-[var(--accent-gold)]/20 border-2 border-[var(--accent-gold)] flex items-center gap-2 text-sm"
                            >
                                <MessageSquare className="w-4 h-4" />
                                Doc Chat
                            </button>
                            <Link
                                href={`/research?matterId=${matterId}`}
                                className="px-5 py-2.5 border border-[var(--border-secondary)] text-[var(--text-secondary)] rounded-xl font-medium hover:border-[var(--accent-gold)] hover:text-[var(--accent-gold)] transition-all flex items-center gap-2 text-sm"
                            >
                                <Search className="w-4 h-4" />
                                Research
                            </Link>
                            <Link
                                href={`/evidence?matterId=${matterId}`}
                                className="px-5 py-2.5 border border-[var(--border-secondary)] text-[var(--text-secondary)] rounded-xl font-medium hover:border-[var(--accent-gold)] hover:text-[var(--accent-gold)] transition-all flex items-center gap-2 text-sm"
                            >
                                <Package className="w-4 h-4" />
                                Evidence
                            </Link>
                            <button
                                onClick={handleDelete}
                                className="px-5 py-2.5 border border-[#ef4444]/30 text-[#ef4444] rounded-xl font-medium hover:bg-[#ef4444]/10 transition-all flex items-center gap-2 text-sm"
                            >
                                <Trash2 className="w-4 h-4" />
                                Delete
                            </button>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 space-y-6">
                        <div className="glass-card p-6 animate-slide-up stagger-1">
                            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-[var(--accent-gold)]" />
                                Matter Information
                            </h2>

                            <div className="grid grid-cols-2 gap-6">
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] transition-colors">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Court</label>
                                    <p className="text-[var(--text-primary)] font-medium">{matter.court || 'Not specified'}</p>
                                </div>
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] transition-colors">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Jurisdiction</label>
                                    <p className="text-[var(--text-primary)] font-medium capitalize">{matter.jurisdiction || 'Not specified'}</p>
                                </div>
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] transition-colors">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Primary Language</label>
                                    <p className="text-[var(--text-primary)] font-medium uppercase">{matter.primary_language || 'MS'}</p>
                                </div>
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] transition-colors">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Estimated Pages</label>
                                    <p className="text-[var(--text-primary)] font-medium">{matter.estimated_pages || 'TBD'}</p>
                                </div>
                            </div>
                        </div>

                        {matter.key_dates && matter.key_dates.length > 0 && (
                            <div className="glass-card p-6 animate-slide-up stagger-2">
                                <div className="flex items-center gap-2 mb-4">
                                    <Calendar className="w-5 h-5 text-[var(--accent-gold)]" />
                                    <h2 className="text-xl font-bold text-[var(--text-primary)]">Key Timeline</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {matter.key_dates.map((date: any, idx: number) => (
                                        <div key={idx} className="flex items-center gap-4 p-3 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border)] hover:border-[var(--accent-gold)]/30 transition-all shadow-sm">
                                            <div className="flex flex-col items-center justify-center w-12 h-12 rounded-lg bg-[var(--accent-gold)]/10 text-[var(--accent-gold)] flex-shrink-0">
                                                <span className="text-[10px] font-bold uppercase">{date.date ? new Date(date.date).toLocaleString('en-US', { month: 'short' }) : '---'}</span>
                                                <span className="text-lg font-black leading-none">{date.date ? new Date(date.date).getDate() : '--'}</span>
                                            </div>
                                            <div className="flex-1 overflow-hidden">
                                                <p className="font-bold text-[var(--text-primary)] text-sm truncate">
                                                    {date.type ? date.type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) : 'Event'}
                                                </p>
                                                <p className="text-xs text-[var(--text-secondary)] truncate">{date.description || 'No details available'}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {matter.parties && matter.parties.length > 0 && (
                            <div className="glass-card p-6 animate-slide-up stagger-2">
                                <div className="flex items-center gap-2 mb-4">
                                    <Users className="w-5 h-5 text-[var(--accent-gold)]" />
                                    <h2 className="text-xl font-bold text-[var(--text-primary)]">Parties</h2>
                                </div>
                                <div className="space-y-3">
                                    {matter.parties.map((party: any, idx: number) => (
                                        <div key={idx} className="border-l-4 border-[var(--accent-gold)] pl-4 py-2 bg-[var(--bg-tertiary)]/50 rounded-r-lg">
                                            <p className="text-[10px] font-bold text-[var(--accent-gold)] uppercase tracking-wider mb-1">{party.role || 'Party'}</p>
                                            <p className="font-bold text-[var(--text-primary)]">{party.name || 'Name not specified'}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {matter.issues && matter.issues.length > 0 && (
                            <div className="glass-card p-6 animate-slide-up stagger-3">
                                <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                    <Zap className="w-5 h-5 text-[var(--accent-gold)]" />
                                    Legal Issues
                                </h2>
                                <div className="space-y-4">
                                    {matter.issues.map((issue: any, idx: number) => (
                                        <div key={idx} className="p-4 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border)] hover:border-[var(--accent-gold)]/30 transition-all group">
                                            <div className="flex items-start gap-3 mb-2">
                                                <div className="w-6 h-6 rounded-full bg-[var(--accent-gold)]/10 flex items-center justify-center flex-shrink-0 mt-0.5 group-hover:bg-[var(--accent-gold)]/20 transition-colors">
                                                    <CheckCircle2 className="w-4 h-4 text-[var(--accent-gold)]" />
                                                </div>,
                                                <div className="flex-1">
                                                    <p className="text-[var(--text-primary)] font-semibold leading-relaxed">
                                                        {issue.text_en || issue.text_ms || issue.text || 'Issue'}
                                                    </p>
                                                </div>
                                            </div>

                                            {(issue.legal_basis || issue.grounds) && (
                                                <div className="ml-9 mt-3 space-y-2.5 pt-3 border-t border-[var(--border)]/50">
                                                    {issue.legal_basis && (
                                                        <div className="flex items-center gap-2">
                                                            <div className="p-1 rounded bg-[var(--accent-gold)]/10">
                                                                <Scale className="w-3 h-3 text-[var(--accent-gold)]" />
                                                            </div>
                                                            <span className="text-[10px] font-bold text-[var(--accent-gold)] uppercase tracking-wider">Legal Basis:</span>
                                                            <span className="text-xs text-[var(--text-secondary)] font-medium">{issue.legal_basis}</span>
                                                        </div>
                                                    )}
                                                    {issue.grounds && (
                                                        <div className="flex items-start gap-2">
                                                            <div className="p-1 rounded bg-[var(--accent-gold)]/10 mt-0.5">
                                                                <FileText className="w-3 h-3 text-[var(--accent-gold)]" />
                                                            </div>
                                                            <div className="flex-1">
                                                                <span className="text-[10px] font-bold text-[var(--accent-gold)] uppercase tracking-wider block mb-0.5">Grounds & Context:</span>
                                                                <p className="text-xs text-[var(--text-secondary)] italic leading-relaxed">{issue.grounds}</p>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {issue.confidence && (
                                                <div className="mt-3 ml-9 flex items-center gap-2 text-[10px]">
                                                    <span className="px-2 py-0.5 rounded-full bg-black/5 text-[var(--text-tertiary)] font-mono border border-black/5">
                                                        AI Confidence: {Math.round(issue.confidence * 100)}%
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {matter.requested_remedies && matter.requested_remedies.length > 0 && (
                            <div className="glass-card p-6 animate-slide-up stagger-3">
                                <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                    <Scale className="w-5 h-5 text-[var(--accent-gold)]" />
                                    Prayers / Relief Sought
                                </h2>
                                <div className="space-y-3">
                                    {matter.requested_remedies.map((remedy: any, idx: number) => (
                                        <div key={idx} className="p-4 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border)] hover:border-[var(--accent-gold)]/30 transition-all group">
                                            <div className="flex items-start gap-3 mb-1">
                                                <div className="w-2 h-2 rounded-full bg-[var(--accent-gold)] mt-2 flex-shrink-0 shadow-[0_0_10px_rgba(212,168,83,0.5)] group-hover:scale-125 transition-transform" />
                                                <div className="flex-1">
                                                    <p className="text-[var(--text-primary)] font-medium">{remedy.text_en || remedy.text || remedy}</p>
                                                </div>
                                                {remedy.amount && (
                                                    <span className="px-2 py-1 bg-[var(--accent-gold)] text-black text-[10px] font-bold rounded-md shadow-sm">
                                                        {remedy.amount}
                                                    </span>
                                                )}
                                            </div>,
                                            {remedy.legal_basis && (
                                                <div className="ml-5 mt-2 flex items-center gap-2 pt-2 border-t border-[var(--border)]/30">
                                                    <span className="text-[9px] font-black text-[var(--text-tertiary)] uppercase tracking-widest">Authority:</span>
                                                    <span className="text-[11px] text-[var(--text-secondary)] italic font-serif">{remedy.legal_basis}</span>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="glass-card p-6 animate-slide-up stagger-4">
                            <div className="flex items-center gap-2 mb-4">
                                <FileText className="w-5 h-5 text-[var(--accent-gold)]" />
                                <h2 className="text-xl font-bold text-[var(--text-primary)]">Documents</h2>
                                <span className="px-2 py-0.5 bg-[var(--accent-gold)]/10 text-[var(--accent-gold)] text-xs font-semibold rounded-full">{documents.length}</span>
                            </div>

                            {documents.length === 0 ? (
                                <div className="text-center py-8">
                                    <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                                        <FileText className="w-6 h-6 text-[var(--text-tertiary)]" />
                                    </div>
                                    <p className="text-[var(--text-secondary)]">No documents uploaded yet</p>
                                </div>
                            ) : (
                                <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
                                    {documents.map((doc: any) => (
                                        <div key={doc.id} className="flex items-center justify-between p-3 border border-[var(--border)] rounded-xl hover:border-[var(--accent-gold)]/30 transition-colors bg-[var(--bg-tertiary)]">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] flex items-center justify-center">
                                                    <FileText className="w-5 h-5 text-[var(--accent-gold)]" />
                                                </div>
                                                <div>
                                                    <p className="font-medium text-[var(--text-primary)] text-sm">{doc.filename}</p>
                                                    <p className="text-xs text-[var(--text-tertiary)]">
                                                        {doc.file_size ? `${Math.round(doc.file_size / 1024)} KB` : 'Unknown size'}
                                                    </p>
                                                </div>
                                            </div>
                                            <button className="w-8 h-8 rounded-lg bg-[var(--bg-secondary)] flex items-center justify-center hover:bg-[var(--accent-gold)]/10 transition-colors">
                                                <Download className="w-4 h-4 text-[var(--text-secondary)]" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="glass-card p-6 animate-slide-up stagger-1">
                            <div className="flex items-center gap-2 mb-4">
                                <AlertCircle className="w-5 h-5 text-[var(--accent-gold)]" />
                                <h2 className="text-xl font-bold text-[var(--text-primary)]">Risk Assessment</h2>
                            </div>

                            <div className="space-y-4">
                                {[
                                    { label: 'Jurisdictional', value: riskScores.jurisdictional_complexity, color: 'accent-gold' },
                                    { label: 'Language', value: riskScores.language_complexity, color: 'accent-gold' },
                                    { label: 'Volume', value: riskScores.volume_risk, color: 'accent-gold' },
                                    { label: 'Time Pressure', value: riskScores.time_pressure, color: 'accent-gold' },
                                ].map((risk, idx) => (
                                    <div key={idx}>
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm text-[var(--text-secondary)]">{risk.label}</span>
                                            <span className="font-bold text-[var(--text-primary)]">{risk.value || 0}/5</span>
                                        </div>
                                        <div className="h-2 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                                            <div
                                                className={`h-full rounded-full bg-[var(--${risk.color})] transition-all duration-500`}
                                                style={{ width: `${((risk.value || 0) / 5) * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                ))}

                                <div className="pt-4 border-t border-[var(--border)]">
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-[var(--text-primary)]">Composite Score</span>
                                        <span className="text-2xl font-bold text-[var(--accent-gold)]">
                                            {riskScores.composite_score ? riskScores.composite_score.toFixed(1) : '0.0'}
                                        </span>
                                    </div>
                                </div>

                                {riskScores.rationale && riskScores.rationale.length > 0 && (
                                    <div className="pt-4 border-t border-[var(--border)]">
                                        <h3 className="text-xs font-semibold text-[var(--text-secondary)] mb-3 flex items-center gap-2">
                                            <Lightbulb className="w-3 h-3 text-[var(--accent-gold)]" />
                                            ANALYSIS EXPLANATION
                                        </h3>
                                        <ul className="space-y-2">
                                            {riskScores.rationale.map((item: string, idx: number) => (
                                                <li key={idx} className="text-xs text-[var(--text-secondary)] flex gap-2 leading-relaxed">
                                                    <span className="text-[var(--accent-gold)] mt-1">•</span>
                                                    {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="glass-card p-6 animate-slide-up stagger-2">
                            <div className="flex items-center gap-2 mb-4">
                                <Target className="w-5 h-5 text-[var(--accent-gold)]" />
                                <h2 className="text-xl font-bold text-[var(--text-primary)]">Case Strength</h2>
                            </div>

                            {!caseStrength ? (
                                <button
                                    onClick={analyzeCaseStrength}
                                    disabled={analyzingStrength}
                                    className="w-full py-3 bg-[var(--accent-gold)] text-black rounded-xl font-bold hover:shadow-lg hover:shadow-[var(--accent-gold)]/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {analyzingStrength ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Analyzing...
                                        </>
                                    ) : (
                                        <>
                                            <Target className="w-5 h-5" />
                                            Analyze Case
                                        </>
                                    )}
                                </button>
                            ) : (
                                <div className="space-y-4">
                                    <div className="text-center">
                                        <div className="relative inline-flex items-center justify-center w-28 h-28">
                                            <svg className="w-28 h-28 transform -rotate-90">
                                                <circle cx="56" cy="56" r="48" stroke="var(--bg-tertiary)" strokeWidth="10" fill="none" />
                                                <circle
                                                    cx="56" cy="56" r="48"
                                                    stroke={caseStrength.win_probability >= 70 ? '#22c55e' : caseStrength.win_probability >= 50 ? '#f97316' : '#ef4444'}
                                                    strokeWidth="10"
                                                    fill="none"
                                                    strokeDasharray={`${(caseStrength.win_probability / 100) * 302} 302`}
                                                    strokeLinecap="round"
                                                />
                                            </svg>
                                            <div className="absolute text-center">
                                                <div className={`text-2xl font-bold ${caseStrength.win_probability >= 70 ? 'text-[#22c55e]' : caseStrength.win_probability >= 50 ? 'text-[#f97316]' : 'text-[#ef4444]'}`}>
                                                    {caseStrength.win_probability}%
                                                </div>
                                                <div className="text-xs text-[var(--text-tertiary)]">Win Prob.</div>
                                            </div>
                                        </div>
                                    </div>

                                    {caseStrength.risks?.length > 0 && (
                                        <div>
                                            <h3 className="text-xs font-semibold text-[#ef4444] flex items-center gap-1 mb-2">
                                                <AlertTriangle className="w-3 h-3" /> Risks
                                            </h3>
                                            <div className="space-y-1">
                                                {caseStrength.risks.slice(0, 2).map((risk: any, idx: number) => (
                                                    <div key={idx} className="text-xs bg-[#ef4444]/5 border border-[#ef4444]/20 rounded-lg p-2 text-[var(--text-secondary)]">
                                                        {risk.risk}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {caseStrength.strengths?.length > 0 && (
                                        <div>
                                            <h3 className="text-xs font-semibold text-[#22c55e] flex items-center gap-1 mb-2">
                                                <Zap className="w-3 h-3" /> Strengths
                                            </h3>
                                            <div className="space-y-1">
                                                {caseStrength.strengths.slice(0, 2).map((strength: any, idx: number) => (
                                                    <div key={idx} className="text-xs bg-[#22c55e]/5 border border-[#22c55e]/20 rounded-lg p-2 text-[var(--text-secondary)]">
                                                        {strength.strength}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <button
                                        onClick={analyzeCaseStrength}
                                        disabled={analyzingStrength}
                                        className="w-full py-2.5 bg-[var(--accent-gold)] text-black rounded-xl text-sm font-bold hover:bg-[#B08D3C] hover:shadow-[0_0_15px_rgba(212,168,83,0.4)] active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
                                    >
                                        {analyzingStrength ? (
                                            <>
                                                <Loader2 className="w-5 h-5 animate-spin" />
                                                Analyzing...
                                            </>
                                        ) : (
                                            <>
                                                <Target className="w-5 h-5" />
                                                Analyze Case
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>

            {/* Doc Chat Slide-over */}
            <AnimatePresence>
                {
                    showParalegalChat && (
                        <>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 0.5 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setShowParalegalChat(false)}
                                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
                            />
                            <motion.div
                                initial={{ x: "100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                                className="fixed top-0 right-0 h-full w-full md:w-[1100px] bg-[var(--bg-secondary)] border-l border-[var(--border)] z-50 shadow-2xl flex flex-col"
                            >
                                <div className="p-4 border-b border-[var(--border-light)] flex justify-between items-center bg-[var(--bg-secondary)]">
                                    <h3 className="font-bold flex items-center gap-2 text-[var(--accent-gold)]">
                                        <Scale className="w-5 h-5" />
                                        Legal Case Assistant
                                    </h3>
                                    <button
                                        onClick={() => setShowParalegalChat(false)}
                                        className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors text-[var(--text-secondary)]"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="flex-1 p-0 overflow-hidden bg-[var(--bg-primary)]">
                                    <ParalegalChat matterId={matterId} />
                                </div>
                            </motion.div>
                        </>
                    )
                }
            </AnimatePresence >
        </div >
    )
}
