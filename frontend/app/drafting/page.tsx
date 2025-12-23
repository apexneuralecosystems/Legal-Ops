'use client'

import { useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Scale, Loader2, CheckCircle2, AlertCircle, FileText, Sparkles, Zap } from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'

function DraftingContent() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const matterId = searchParams.get('matterId') || searchParams.get('matter')

    const [selectedTemplate, setSelectedTemplate] = useState('TPL-HighCourt-MS-v2')
    const [selectedIssues, setSelectedIssues] = useState<any[]>([])
    const [selectedPrayers, setSelectedPrayers] = useState<any[]>([])

    const { data: matter } = useQuery({
        queryKey: ['matter', matterId],
        queryFn: () => matterId ? api.getMatter(matterId) : null,
        enabled: !!matterId,
    })

    const draftingMutation = useMutation({
        mutationFn: async () => {
            if (!matterId) throw new Error('No matter selected')
            return api.startDraftingWorkflow(matterId, {
                template_id: selectedTemplate,
                issues_selected: selectedIssues,
                prayers_selected: selectedPrayers,
            })
        },
    })

    const templates = [
        { id: 'TPL-HighCourt-MS-v2', name: 'High Court Statement of Claim (Malay)', language: 'ms', gradient: 'from-[var(--neon-orange)] to-[var(--neon-red)]' },
        { id: 'TPL-HighCourt-EN-v2', name: 'High Court Statement of Claim (English)', language: 'en', gradient: 'from-[var(--neon-cyan)] to-[var(--neon-blue)]' },
    ]

    const matterIssues = matter?.issues || []
    const displayIssues = matterIssues.length > 0 ? matterIssues.map((issue: any, idx: number) => ({
        id: issue.id || `ISS-${idx + 1}`,
        title: issue.text_en || issue.title || `[Issue ${idx + 1} - Please specify]`,
        legal_basis: issue.legal_basis || ['[Legal basis to be specified]']
    })) : [
        { id: 'ISS-01', title: '[Please specify the legal issue / Sila nyatakan isu undang-undang]', legal_basis: ['[Legal basis / Asas undang-undang]'] }
    ]

    const matterRemedies = matter?.requested_remedies || []
    const displayPrayers = matterRemedies.length > 0 ? matterRemedies.map((remedy: any) => ({
        text_en: remedy.text || remedy.text_en || '[Remedy description]',
        text_ms: remedy.text_ms || '[Deskripsi remedi]'
    })) : [
        { text_en: '[Judgment for RM ______]', text_ms: '[Penghakiman untuk RM ______]' },
        { text_en: '[Interest and costs]', text_ms: '[Faedah dan kos]' }
    ]

    const toggleIssue = (issue: any) => {
        if (selectedIssues.find(i => i.id === issue.id)) {
            setSelectedIssues(selectedIssues.filter(i => i.id !== issue.id))
        } else {
            setSelectedIssues([...selectedIssues, issue])
        }
    }

    const togglePrayer = (prayer: any) => {
        if (selectedPrayers.find(p => p.text_en === prayer.text_en)) {
            setSelectedPrayers(selectedPrayers.filter(p => p.text_en !== prayer.text_en))
        } else {
            setSelectedPrayers([...selectedPrayers, prayer])
        }
    }

    if (!matterId) {
        return (
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <div className="card p-12 text-center max-w-md">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--neon-orange)]/10 flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-[var(--neon-orange)]" />
                        </div>
                        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">No Matter Selected</h2>
                        <p className="text-[var(--text-secondary)] mb-6">Please select a matter from the dashboard to start drafting.</p>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="btn-primary inline-flex items-center gap-2 px-6 py-3"
                        >
                            <Sparkles className="w-5 h-5" />
                            Go to Dashboard
                        </button>
                    </div>
                </main>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />
            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-pink)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--neon-purple)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                <div className="mb-10 animate-fade-in">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="icon-box w-12 h-12">
                            <Scale className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold gradient-text">Drafting Workflow</h1>
                            <p className="text-[var(--text-secondary)] mt-1">Generate bilingual legal pleadings with AI</p>
                        </div>
                    </div>
                    <div className="cyber-line mt-6"></div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
                    <div className="lg:col-span-1 space-y-6">
                        <div className="card p-6 animate-slide-up">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-[var(--neon-cyan)]" />
                                Template
                            </h2>
                            <div className="space-y-3">
                                {templates.map(template => (
                                    <button
                                        key={template.id}
                                        onClick={() => setSelectedTemplate(template.id)}
                                        className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-300 ${
                                            selectedTemplate === template.id
                                                ? 'border-[var(--neon-purple)] bg-[var(--neon-purple)]/5'
                                                : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                        }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${template.gradient} flex items-center justify-center`}>
                                                <FileText className="w-5 h-5 text-white" />
                                            </div>
                                            <div className="flex-1">
                                                <div className={`font-medium ${selectedTemplate === template.id ? 'text-[var(--neon-purple)]' : 'text-[var(--text-primary)]'}`}>
                                                    {template.name}
                                                </div>
                                                <div className="text-xs text-[var(--text-tertiary)]">
                                                    {template.language === 'ms' ? 'Bahasa Malaysia' : 'English'}
                                                </div>
                                            </div>
                                            {selectedTemplate === template.id && (
                                                <div className="w-3 h-3 bg-[var(--neon-green)] rounded-full"></div>
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="card p-6 animate-slide-up stagger-1">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-[var(--neon-orange)]" />
                                Issues ({selectedIssues.length})
                            </h2>
                            <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                                {displayIssues.map((issue: any) => (
                                    <label
                                        key={issue.id}
                                        className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                                            selectedIssues.find(i => i.id === issue.id)
                                                ? 'border-[var(--neon-orange)] bg-[var(--neon-orange)]/5'
                                                : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                        }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={!!selectedIssues.find(i => i.id === issue.id)}
                                            onChange={() => toggleIssue(issue)}
                                            className="mt-1 accent-[var(--neon-orange)]"
                                        />
                                        <div className="font-medium text-sm text-[var(--text-primary)]">{issue.title}</div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="card p-6 animate-slide-up stagger-2">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-[var(--neon-pink)]" />
                                Prayers ({selectedPrayers.length})
                            </h2>
                            <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                                {displayPrayers.map((prayer: any, idx: number) => (
                                    <label
                                        key={idx}
                                        className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                                            selectedPrayers.find(p => p.text_en === prayer.text_en)
                                                ? 'border-[var(--neon-pink)] bg-[var(--neon-pink)]/5'
                                                : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                        }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={!!selectedPrayers.find(p => p.text_en === prayer.text_en)}
                                            onChange={() => togglePrayer(prayer)}
                                            className="mt-1 accent-[var(--neon-pink)]"
                                        />
                                        <div className="text-sm text-[var(--text-primary)]">{prayer.text_en}</div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={() => draftingMutation.mutate()}
                            disabled={selectedIssues.length === 0 || draftingMutation.isPending}
                            className="w-full btn-primary py-4 flex items-center justify-center gap-2 animate-slide-up stagger-3"
                        >
                            {draftingMutation.isPending ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <Scale className="w-5 h-5" />
                                    Generate Pleading
                                </>
                            )}
                        </button>
                    </div>

                    <div className="lg:col-span-2">
                        <div className="card p-6 h-full animate-slide-up stagger-2">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-[var(--neon-purple)]" />
                                Preview
                            </h2>
                            
                            {draftingMutation.data ? (
                                <div className="space-y-6">
                                    {draftingMutation.data.workflow_result?.qa_report && (
                                        <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--neon-green)]/10 border border-[var(--neon-green)]/20">
                                            <CheckCircle2 className="w-5 h-5 text-[var(--neon-green)]" />
                                            <span className="font-medium text-[var(--neon-green)]">QA Validation Passed</span>
                                        </div>
                                    )}
                                    
                                    <div className="p-4 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] max-h-[500px] overflow-y-auto">
                                        <pre className="whitespace-pre-wrap text-sm text-[var(--text-secondary)] font-mono">
                                            {draftingMutation.data.workflow_result?.pleading_ms?.pleading_ms_text || 'Pleading generated successfully'}
                                        </pre>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-20">
                                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                                        <Scale className="w-10 h-10 text-[var(--text-tertiary)]" />
                                    </div>
                                    <p className="text-[var(--text-secondary)]">Select template, issues, and prayers to generate pleading</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default function DraftingPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-[var(--neon-cyan)]" />
                </main>
            </div>
        }>
            <DraftingContent />
        </Suspense>
    )
}
