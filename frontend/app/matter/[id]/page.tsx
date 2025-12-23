'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { ArrowLeft, FileText, Calendar, Users, AlertCircle, CheckCircle2, Download, Trash2, Target, AlertTriangle, Zap, Lightbulb, Loader2, Sparkles, Shield, Scale, Search, Package } from 'lucide-react'
import Link from 'next/link'

import { api } from '@/lib/api'

export default function MatterDetailPage() {
    const params = useParams()
    const router = useRouter()
    const matterId = params.id as string

    const [matter, setMatter] = useState<any>(null)
    const [documents, setDocuments] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [caseStrength, setCaseStrength] = useState<any>(null)
    const [analyzingStrength, setAnalyzingStrength] = useState(false)

    useEffect(() => {
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
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-cyan)] flex items-center justify-center shadow-lg animate-pulse">
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
                    <div className="card p-12 text-center max-w-md">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--neon-red)]/10 flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-[var(--neon-red)]" />
                        </div>
                        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Matter not found</h2>
                        <p className="text-[var(--text-secondary)] mb-6">The matter you're looking for doesn't exist.</p>
                        <Link href="/dashboard" className="btn-primary inline-flex items-center gap-2 px-6 py-3">
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
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-purple)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--neon-cyan)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--neon-cyan)] mb-6 transition-colors animate-fade-in"
                >
                    <ArrowLeft className="w-5 h-5" />
                    <span className="font-medium">Back</span>
                </button>

                <div className="mb-8 animate-slide-up">
                    <div className="flex items-start justify-between mb-4 flex-wrap gap-4">
                        <div>
                            <div className="flex items-center gap-3 mb-2 flex-wrap">
                                <h1 className="text-3xl font-bold gradient-text">{matter.title}</h1>
                                {matter.human_review_required && (
                                    <span className="px-3 py-1 bg-[var(--neon-orange)]/10 text-[var(--neon-orange)] text-xs font-semibold rounded-full border border-[var(--neon-orange)]/20">
                                        Requires Review
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)] flex-wrap">
                                <span className="font-mono px-2 py-1 bg-[var(--bg-tertiary)] rounded">{matter.matter_id}</span>
                                <span className="capitalize">{matter.matter_type?.replace('_', ' ')}</span>
                                <span className="px-2 py-1 bg-[var(--neon-cyan)]/10 text-[var(--neon-cyan)] rounded capitalize">{matter.status}</span>
                            </div>
                        </div>
                        <div className="flex gap-3 flex-wrap">
                            <Link
                                href={`/drafting?matterId=${matterId}`}
                                className="btn-primary px-5 py-2.5 flex items-center gap-2 text-sm"
                            >
                                <Scale className="w-4 h-4" />
                                Drafting
                            </Link>
                            <Link
                                href={`/research?matterId=${matterId}`}
                                className="px-5 py-2.5 border border-[var(--border-secondary)] text-[var(--text-secondary)] rounded-xl font-medium hover:border-[var(--neon-cyan)] hover:text-[var(--neon-cyan)] transition-all flex items-center gap-2 text-sm"
                            >
                                <Search className="w-4 h-4" />
                                Research
                            </Link>
                            <Link
                                href={`/evidence?matterId=${matterId}`}
                                className="px-5 py-2.5 border border-[var(--border-secondary)] text-[var(--text-secondary)] rounded-xl font-medium hover:border-[var(--neon-purple)] hover:text-[var(--neon-purple)] transition-all flex items-center gap-2 text-sm"
                            >
                                <Package className="w-4 h-4" />
                                Evidence
                            </Link>
                            <button
                                onClick={handleDelete}
                                className="px-5 py-2.5 border border-[var(--neon-red)]/30 text-[var(--neon-red)] rounded-xl font-medium hover:bg-[var(--neon-red)]/10 transition-all flex items-center gap-2 text-sm"
                            >
                                <Trash2 className="w-4 h-4" />
                                Delete
                            </button>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 space-y-6">
                        <div className="card p-6 animate-slide-up stagger-1">
                            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-[var(--neon-cyan)]" />
                                Matter Information
                            </h2>

                            <div className="grid grid-cols-2 gap-6">
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)]">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Court</label>
                                    <p className="text-[var(--text-primary)] font-medium">{matter.court || 'Not specified'}</p>
                                </div>
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)]">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Jurisdiction</label>
                                    <p className="text-[var(--text-primary)] font-medium capitalize">{matter.jurisdiction || 'Not specified'}</p>
                                </div>
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)]">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Primary Language</label>
                                    <p className="text-[var(--text-primary)] font-medium uppercase">{matter.primary_language || 'MS'}</p>
                                </div>
                                <div className="p-3 rounded-lg bg-[var(--bg-tertiary)]">
                                    <label className="text-xs font-medium text-[var(--text-tertiary)] block mb-1">Estimated Pages</label>
                                    <p className="text-[var(--text-primary)] font-medium">{matter.estimated_pages || 'TBD'}</p>
                                </div>
                            </div>
                        </div>

                        {matter.parties && matter.parties.length > 0 && (
                            <div className="card p-6 animate-slide-up stagger-2">
                                <div className="flex items-center gap-2 mb-4">
                                    <Users className="w-5 h-5 text-[var(--neon-purple)]" />
                                    <h2 className="text-xl font-bold text-[var(--text-primary)]">Parties</h2>
                                </div>
                                <div className="space-y-3">
                                    {matter.parties.map((party: any, idx: number) => (
                                        <div key={idx} className="border-l-2 border-[var(--neon-purple)] pl-4 py-2">
                                            <p className="font-medium text-[var(--text-primary)] capitalize">{party.role || 'Party'}</p>
                                            <p className="text-sm text-[var(--text-secondary)]">{party.name || 'Name not specified'}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {matter.issues && matter.issues.length > 0 && (
                            <div className="card p-6 animate-slide-up stagger-3">
                                <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                    <Zap className="w-5 h-5 text-[var(--neon-orange)]" />
                                    Legal Issues
                                </h2>
                                <div className="space-y-3">
                                    {matter.issues.map((issue: any, idx: number) => (
                                        <div key={idx} className="flex items-start gap-3 p-3 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-primary)]">
                                            <CheckCircle2 className="w-5 h-5 text-[var(--neon-green)] mt-0.5 flex-shrink-0" />
                                            <div className="flex-1">
                                                <p className="text-[var(--text-primary)]">{issue.text_en || issue.text_ms || issue.text || 'Issue'}</p>
                                                {issue.confidence && (
                                                    <p className="text-xs text-[var(--text-tertiary)] mt-1">Confidence: {Math.round(issue.confidence * 100)}%</p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="card p-6 animate-slide-up stagger-4">
                            <div className="flex items-center gap-2 mb-4">
                                <FileText className="w-5 h-5 text-[var(--neon-cyan)]" />
                                <h2 className="text-xl font-bold text-[var(--text-primary)]">Documents</h2>
                                <span className="px-2 py-0.5 bg-[var(--neon-cyan)]/10 text-[var(--neon-cyan)] text-xs font-semibold rounded-full">{documents.length}</span>
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
                                        <div key={doc.id} className="flex items-center justify-between p-3 border border-[var(--border-primary)] rounded-xl hover:border-[var(--neon-cyan)]/30 transition-colors bg-[var(--bg-tertiary)]">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[var(--neon-blue)] to-[var(--neon-purple)] flex items-center justify-center">
                                                    <FileText className="w-5 h-5 text-white" />
                                                </div>
                                                <div>
                                                    <p className="font-medium text-[var(--text-primary)] text-sm">{doc.filename}</p>
                                                    <p className="text-xs text-[var(--text-tertiary)]">
                                                        {doc.file_size ? `${Math.round(doc.file_size / 1024)} KB` : 'Unknown size'}
                                                    </p>
                                                </div>
                                            </div>
                                            <button className="w-8 h-8 rounded-lg bg-[var(--bg-secondary)] flex items-center justify-center hover:bg-[var(--neon-cyan)]/10 transition-colors">
                                                <Download className="w-4 h-4 text-[var(--text-secondary)]" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="card p-6 animate-slide-up stagger-1">
                            <div className="flex items-center gap-2 mb-4">
                                <AlertCircle className="w-5 h-5 text-[var(--neon-red)]" />
                                <h2 className="text-xl font-bold text-[var(--text-primary)]">Risk Assessment</h2>
                            </div>

                            <div className="space-y-4">
                                {[
                                    { label: 'Jurisdictional', value: riskScores.jurisdictional_complexity, color: 'neon-purple' },
                                    { label: 'Language', value: riskScores.language_complexity, color: 'neon-cyan' },
                                    { label: 'Volume', value: riskScores.volume_risk, color: 'neon-orange' },
                                    { label: 'Time Pressure', value: riskScores.time_pressure, color: 'neon-red' },
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

                                <div className="pt-4 border-t border-[var(--border-primary)]">
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-[var(--text-primary)]">Composite Score</span>
                                        <span className="text-2xl font-bold text-[var(--neon-cyan)]">
                                            {riskScores.composite_score ? riskScores.composite_score.toFixed(1) : '0.0'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="card p-6 animate-slide-up stagger-2">
                            <div className="flex items-center gap-2 mb-4">
                                <Target className="w-5 h-5 text-[var(--neon-purple)]" />
                                <h2 className="text-xl font-bold text-[var(--text-primary)]">Case Strength</h2>
                            </div>

                            {!caseStrength ? (
                                <button
                                    onClick={analyzeCaseStrength}
                                    disabled={analyzingStrength}
                                    className="w-full py-3 bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] text-white rounded-xl font-medium hover:shadow-lg hover:shadow-[var(--neon-purple)]/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
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
                                                    stroke={caseStrength.win_probability >= 70 ? 'var(--neon-green)' : caseStrength.win_probability >= 50 ? 'var(--neon-orange)' : 'var(--neon-red)'}
                                                    strokeWidth="10"
                                                    fill="none"
                                                    strokeDasharray={`${(caseStrength.win_probability / 100) * 302} 302`}
                                                    strokeLinecap="round"
                                                />
                                            </svg>
                                            <div className="absolute text-center">
                                                <div className={`text-2xl font-bold ${caseStrength.win_probability >= 70 ? 'text-[var(--neon-green)]' : caseStrength.win_probability >= 50 ? 'text-[var(--neon-orange)]' : 'text-[var(--neon-red)]'}`}>
                                                    {caseStrength.win_probability}%
                                                </div>
                                                <div className="text-xs text-[var(--text-tertiary)]">Win Prob.</div>
                                            </div>
                                        </div>
                                    </div>

                                    {caseStrength.risks?.length > 0 && (
                                        <div>
                                            <h3 className="text-xs font-semibold text-[var(--neon-red)] flex items-center gap-1 mb-2">
                                                <AlertTriangle className="w-3 h-3" /> Risks
                                            </h3>
                                            <div className="space-y-1">
                                                {caseStrength.risks.slice(0, 2).map((risk: any, idx: number) => (
                                                    <div key={idx} className="text-xs bg-[var(--neon-red)]/5 border border-[var(--neon-red)]/20 rounded-lg p-2 text-[var(--text-secondary)]">
                                                        {risk.risk}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {caseStrength.strengths?.length > 0 && (
                                        <div>
                                            <h3 className="text-xs font-semibold text-[var(--neon-green)] flex items-center gap-1 mb-2">
                                                <Zap className="w-3 h-3" /> Strengths
                                            </h3>
                                            <div className="space-y-1">
                                                {caseStrength.strengths.slice(0, 2).map((strength: any, idx: number) => (
                                                    <div key={idx} className="text-xs bg-[var(--neon-green)]/5 border border-[var(--neon-green)]/20 rounded-lg p-2 text-[var(--text-secondary)]">
                                                        {strength.strength}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <button
                                        onClick={analyzeCaseStrength}
                                        disabled={analyzingStrength}
                                        className="w-full py-2 border border-[var(--neon-purple)]/30 text-[var(--neon-purple)] rounded-xl text-sm font-medium hover:bg-[var(--neon-purple)]/5 transition-colors"
                                    >
                                        Re-analyze
                                    </button>
                                </div>
                            )}
                        </div>

                        {matter.key_dates && matter.key_dates.length > 0 && (
                            <div className="card p-6 animate-slide-up stagger-3">
                                <div className="flex items-center gap-2 mb-4">
                                    <Calendar className="w-5 h-5 text-[var(--neon-orange)]" />
                                    <h2 className="text-xl font-bold text-[var(--text-primary)]">Key Dates</h2>
                                </div>
                                <div className="space-y-3">
                                    {matter.key_dates.map((date: any, idx: number) => (
                                        <div key={idx} className="flex items-start gap-3">
                                            <div className="w-2 h-2 rounded-full bg-[var(--neon-orange)] mt-2 flex-shrink-0" />
                                            <div>
                                                <p className="font-medium text-[var(--text-primary)] capitalize text-sm">{date.type || 'Date'}</p>
                                                <p className="text-xs text-[var(--text-secondary)]">{date.date || 'Date not specified'}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    )
}
