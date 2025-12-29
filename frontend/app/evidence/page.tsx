'use client'

import { useState, useRef, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Package, Loader2, FileText, CheckCircle2, Download, Scale, Volume2, Square, Sparkles, FolderOpen, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'

function EvidenceContent() {
    const searchParams = useSearchParams()
    const matterId = searchParams.get('matterId') || searchParams.get('matter')

    const [selectedDocs, setSelectedDocs] = useState<string[]>([])
    const [isSpeaking, setIsSpeaking] = useState(false)
    const [currentSection, setCurrentSection] = useState<string>('')
    const speechRef = useRef<SpeechSynthesisUtterance | null>(null)

    const { data: documents, isLoading: docsLoading } = useQuery({
        queryKey: ['matter-documents', matterId],
        queryFn: async () => {
            if (!matterId) return null
            return api.getMatterDocuments(matterId)
        },
        enabled: !!matterId,
    })

    const evidenceMutation = useMutation({
        mutationFn: async () => {
            if (!matterId) throw new Error('No matter selected')
            const docs = documents?.filter((d: any) => selectedDocs.includes(d.id)) || []
            return api.buildEvidencePacket(matterId, docs)
        },
    })

    const hearingMutation = useMutation({
        mutationFn: async () => {
            if (!matterId) throw new Error('No matter selected')
            return api.prepareHearing(matterId)
        },
    })

    const toggleDoc = (docId: string) => {
        if (selectedDocs.includes(docId)) {
            setSelectedDocs(selectedDocs.filter(id => id !== docId))
        } else {
            setSelectedDocs([...selectedDocs, docId])
        }
    }

    const downloadHearingBundlePDF = () => {
        const data = hearingMutation.data
        if (!data?.hearing_bundle) return

        const content = `HEARING BUNDLE\n==============\nMatter: ${matterId}\nGenerated: ${new Date().toLocaleString()}\n\n${'='.repeat(50)}\nBUNDLE STRUCTURE\n${'='.repeat(50)}\n${data.hearing_bundle?.tabs?.map((tab: any) =>
            `Tab ${tab.tab}: ${tab.section}\n${tab.items?.length ? tab.items.map((i: any) => `  - ${i.description} (${i.language})`).join('\n') : '  (No items yet)'}`
        ).join('\n\n') || '(No tabs defined)'}\n\n${'='.repeat(50)}\nSKRIP HUJAHAN LISAN (MALAY)\n${'='.repeat(50)}\n${data.hearing_bundle?.oral_script_ms || '(No Malay script available)'}\n\n${'='.repeat(50)}\nENGLISH NOTES\n${'='.repeat(50)}\n${data.hearing_bundle?.oral_script_en_notes || '(No English notes available)'}`

        const blob = new Blob([content], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `hearing_bundle_${matterId}.txt`
        a.click()
        URL.revokeObjectURL(url)
    }

    const stopSpeaking = () => {
        window.speechSynthesis.cancel()
        setIsSpeaking(false)
        setCurrentSection('')
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
                        <p className="text-[var(--text-secondary)] mb-6">
                            Please select a matter from the Dashboard to prepare evidence and hearing materials.
                        </p>
                        <a href="/dashboard" className="btn-primary inline-flex items-center gap-2 px-6 py-3">
                            <FolderOpen className="w-5 h-5" />
                            Go to Dashboard
                        </a>
                    </div>
                </main>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />
            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-purple)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--neon-orange)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                <div className="mb-10 animate-fade-in">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="icon-box w-12 h-12">
                            <Package className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold gradient-text">Evidence & Hearing</h1>
                            <p className="text-[var(--text-secondary)] mt-1">Prepare court bundles and hearing materials</p>
                        </div>
                    </div>
                    <div className="cyber-line mt-6"></div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
                    <div className="lg:col-span-1 space-y-6">
                        <div className="card p-6 animate-slide-up">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-[var(--neon-cyan)]" />
                                Documents ({selectedDocs.length}/{documents?.length || 0})
                            </h2>

                            {docsLoading ? (
                                <div className="flex justify-center py-8">
                                    <Loader2 className="w-8 h-8 animate-spin text-[var(--neon-cyan)]" />
                                </div>
                            ) : documents && documents.length > 0 ? (
                                <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
                                    {documents.map((doc: any) => (
                                        <label
                                            key={doc.id}
                                            className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${selectedDocs.includes(doc.id)
                                                ? 'border-[var(--neon-cyan)] bg-[var(--neon-cyan)]/5'
                                                : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                                }`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedDocs.includes(doc.id)}
                                                onChange={() => toggleDoc(doc.id)}
                                                className="mt-1 accent-[var(--neon-cyan)]"
                                            />
                                            <div className="flex-1 min-w-0">
                                                <div className="font-medium text-sm text-[var(--text-primary)] truncate">{doc.filename}</div>
                                                <div className="text-xs text-[var(--text-tertiary)]">{doc.mime_type}</div>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-[var(--text-tertiary)] text-sm text-center py-4">No documents available</p>
                            )}
                        </div>

                        <div className="space-y-3 animate-slide-up stagger-1">
                            <button
                                onClick={() => evidenceMutation.mutate()}
                                disabled={selectedDocs.length === 0 || evidenceMutation.isPending}
                                className="w-full btn-primary py-3 flex items-center justify-center gap-2"
                            >
                                {evidenceMutation.isPending ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Building...
                                    </>
                                ) : (
                                    <>
                                        <Package className="w-5 h-5" />
                                        Build Evidence Packet
                                    </>
                                )}
                            </button>

                            <button
                                onClick={() => hearingMutation.mutate()}
                                disabled={hearingMutation.isPending}
                                className="w-full px-6 py-3 bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-[var(--neon-purple)]/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {hearingMutation.isPending ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Preparing...
                                    </>
                                ) : (
                                    <>
                                        <Scale className="w-5 h-5" />
                                        Prepare Hearing Bundle
                                    </>
                                )}
                            </button>
                        </div>

                        {/* Error Messages */}
                        {(evidenceMutation.isError || hearingMutation.isError) && (
                            <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                                <div className="font-bold flex items-center gap-2 mb-1">
                                    <AlertCircle className="w-4 h-4" />
                                    Error
                                </div>
                                {evidenceMutation.error?.message || hearingMutation.error?.message || 'An error occurred'}
                            </div>
                        )}
                    </div>

                    <div className="lg:col-span-2">
                        <div className="card p-6 animate-slide-up stagger-2">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-[var(--neon-purple)]" />
                                Preview
                            </h2>

                            {evidenceMutation.data ? (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--neon-green)]/10 border border-[var(--neon-green)]/20">
                                        <CheckCircle2 className="w-5 h-5 text-[var(--neon-green)]" />
                                        <span className="font-medium text-[var(--neon-green)]">Evidence Packet Created</span>
                                    </div>

                                    <div>
                                        <h3 className="font-semibold text-[var(--text-primary)] mb-3">Evidence Index</h3>
                                        <div className="rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] p-4">
                                            {evidenceMutation.data.evidence_packet?.exhibit_index?.map((exhibit: any, idx: number) => (
                                                <div key={idx} className="flex items-center gap-3 py-2 border-b border-[var(--border-primary)] last:border-b-0">
                                                    <span className="font-mono font-bold text-[var(--neon-cyan)] w-16">{exhibit.exhibit_id}</span>
                                                    <div className="flex-1">
                                                        <div className="font-medium text-sm text-[var(--text-primary)]">{exhibit.description}</div>
                                                        <div className="text-xs text-[var(--text-tertiary)]">{exhibit.document_type} | Pages: {exhibit.pages}</div>
                                                    </div>
                                                </div>
                                            )) || <div className="text-[var(--text-tertiary)] text-sm">No exhibits added</div>}
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-[var(--neon-purple)]/10 to-transparent border border-[var(--neon-purple)]/20 text-center">
                                            <div className="text-2xl font-bold text-[var(--neon-purple)]">
                                                {evidenceMutation.data.evidence_packet?.total_exhibits || 0}
                                            </div>
                                            <div className="text-xs text-[var(--text-secondary)]">Total Exhibits</div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-[var(--neon-orange)]/10 to-transparent border border-[var(--neon-orange)]/20 text-center">
                                            <div className="text-2xl font-bold text-[var(--neon-orange)]">
                                                {evidenceMutation.data.evidence_packet?.total_pages || 'TBD'}
                                            </div>
                                            <div className="text-xs text-[var(--text-secondary)]">Total Pages</div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-[var(--neon-green)]/10 to-transparent border border-[var(--neon-green)]/20 text-center">
                                            <div className="text-2xl font-bold text-[var(--neon-green)]">
                                                {selectedDocs.length}
                                            </div>
                                            <div className="text-xs text-[var(--text-secondary)]">Selected</div>
                                        </div>
                                    </div>
                                </div>
                            ) : hearingMutation.data ? (
                                <div className="space-y-6">
                                    <div className="flex items-center justify-between flex-wrap gap-3">
                                        <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--neon-green)]/10 border border-[var(--neon-green)]/20">
                                            <CheckCircle2 className="w-5 h-5 text-[var(--neon-green)]" />
                                            <span className="font-medium text-[var(--neon-green)]">Hearing Bundle Prepared</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {isSpeaking ? (
                                                <button onClick={stopSpeaking} className="flex items-center gap-2 px-4 py-2 bg-[var(--neon-red)] text-white rounded-xl text-sm font-medium">
                                                    <Square className="w-4 h-4" />
                                                    Stop
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => {
                                                        const script = hearingMutation.data?.hearing_bundle?.oral_script_ms
                                                            ? `Bahasa Malaysia Script. ${hearingMutation.data.hearing_bundle.oral_script_ms}. English Notes. ${hearingMutation.data.hearing_bundle.oral_script_en_notes || ''}`
                                                            : 'No script available to read.'

                                                        const utterance = new SpeechSynthesisUtterance(script)
                                                        utterance.onend = () => {
                                                            setIsSpeaking(false)
                                                            setCurrentSection('')
                                                        }

                                                        setIsSpeaking(true)
                                                        setCurrentSection('Oral Submission Script')
                                                        window.speechSynthesis.speak(utterance)
                                                    }}
                                                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] text-white rounded-xl text-sm font-medium hover:opacity-90 transition-opacity"
                                                >
                                                    <Volume2 className="w-4 h-4" />
                                                    Listen
                                                </button>
                                            )}
                                            <button onClick={downloadHearingBundlePDF} className="flex items-center gap-2 px-4 py-2 bg-[var(--neon-blue)] text-white rounded-xl text-sm font-medium">
                                                <Download className="w-4 h-4" />
                                                Download
                                            </button>
                                        </div>
                                    </div>

                                    {isSpeaking && currentSection && (
                                        <div className="flex items-center gap-3 p-3 rounded-xl bg-[var(--neon-purple)]/10 border border-[var(--neon-purple)]/20">
                                            <div className="w-3 h-3 bg-[var(--neon-purple)] rounded-full animate-pulse"></div>
                                            <span className="text-[var(--neon-purple)] font-medium">Now reading: {currentSection}</span>
                                        </div>
                                    )}

                                    <div>
                                        <h3 className="font-semibold text-[var(--text-primary)] mb-3">Bundle Structure</h3>
                                        <div className="space-y-2">
                                            {hearingMutation.data.hearing_bundle?.tabs?.map((tab: any, idx: number) => (
                                                <div key={idx} className="p-3 rounded-xl bg-[var(--bg-tertiary)] border-l-4 border-[var(--neon-blue)]">
                                                    <div className="font-medium text-[var(--text-primary)]">Tab {tab.tab}: {tab.section}</div>
                                                    {tab.items?.length > 0 && (
                                                        <ul className="mt-2 text-sm text-[var(--text-secondary)] space-y-1">
                                                            {tab.items.map((item: any, i: number) => (
                                                                <li key={i}>• {item.description} ({item.language})</li>
                                                            ))}
                                                        </ul>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="font-semibold text-[var(--text-primary)] mb-3">Skrip Hujahan Lisan (Malay)</h3>
                                        <div className="p-4 rounded-xl bg-[var(--neon-orange)]/5 border border-[var(--neon-orange)]/20">
                                            <pre className="text-sm whitespace-pre-wrap text-[var(--text-secondary)]">
                                                {hearingMutation.data.hearing_bundle?.oral_script_ms || '(Script will be generated)'}
                                            </pre>
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="font-semibold text-[var(--text-primary)] mb-3">English Notes</h3>
                                        <div className="p-4 rounded-xl bg-[var(--neon-cyan)]/5 border border-[var(--neon-cyan)]/20">
                                            <pre className="text-sm whitespace-pre-wrap text-[var(--text-secondary)]">
                                                {hearingMutation.data.hearing_bundle?.oral_script_en_notes || '(Notes will be generated)'}
                                            </pre>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-20">
                                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                                        <Package className="w-10 h-10 text-[var(--text-tertiary)]" />
                                    </div>
                                    <p className="text-[var(--text-secondary)]">Select documents and build evidence packet or prepare hearing</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default function EvidencePage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-[var(--neon-cyan)]" />
                </main>
            </div>
        }>
            <EvidenceContent />
        </Suspense>
    )
}
