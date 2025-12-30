// Evidence & Hearing Page - Professional Legal View
// This component displays hearing bundles in a formal, court-ready format

'use client'

import React, { useState, useRef, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
    Package, Loader2, FileText, CheckCircle2, Download, Scale,
    Volume2, Square, Sparkles, FolderOpen, AlertCircle,
    Gavel, BookOpen, FileCheck, Printer
} from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'

function EvidenceContent() {
    const searchParams = useSearchParams()
    const matterId = searchParams.get('matterId') || searchParams.get('matter')

    const [selectedDocs, setSelectedDocs] = useState<string[]>([])
    const [isSpeaking, setIsSpeaking] = useState(false)
    const [currentSection, setCurrentSection] = useState<string>('')
    const speechRef = useRef<SpeechSynthesisUtterance | null>(null)

    const { data: matterData } = useQuery({
        queryKey: ['matter', matterId],
        queryFn: async () => {
            if (!matterId) return null
            return api.getMatter(matterId)
        },
        enabled: !!matterId,
    })

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

        // Generate formal legal document
        const content = `
═══════════════════════════════════════════════════════════════════
                        HEARING BUNDLE
═══════════════════════════════════════════════════════════════════

Matter Reference: ${matterId}
Date Generated: ${new Date().toLocaleString('en-MY', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })}

${data.hearing_bundle?.bundle_name || 'HEARING BUNDLE'}

═══════════════════════════════════════════════════════════════════
                        TABLE OF CONTENTS
═══════════════════════════════════════════════════════════════════

${data.hearing_bundle?.tabs?.map((tab: any) =>
            `TAB ${tab.tab}: ${tab.section.toUpperCase()}
${tab.items?.length ? tab.items.map((i: any, idx: number) =>
                `    ${idx + 1}. ${i.description} (${i.language})`
            ).join('\n') : '    (No items yet)'}`
        ).join('\n\n') || '(No tabs defined)'}

═══════════════════════════════════════════════════════════════════
                    SKRIP HUJAHAN LISAN (BAHASA MALAYSIA)
═══════════════════════════════════════════════════════════════════

${data.hearing_bundle?.oral_script_ms || '(Script to be prepared)'}

═══════════════════════════════════════════════════════════════════
                        ENGLISH COMPANION NOTES
═══════════════════════════════════════════════════════════════════

${data.hearing_bundle?.oral_script_en_notes || '(Notes to be prepared)'}

═══════════════════════════════════════════════════════════════════
                        ANTICIPATED QUESTIONS
═══════════════════════════════════════════════════════════════════

${data.hearing_bundle?.if_judge_asks?.map((qa: any, idx: number) =>
            `${idx + 1}. Q: ${qa.question}
   
   A (Malay): ${qa.answer_ms}
   
   A (English): ${qa.answer_en}
   
   Authority: ${qa.authority}
   Confidence: ${(qa.confidence * 100).toFixed(0)}%`
        ).join('\n\n═══════════════════════════════════════════════════════════════════\n\n') || '(To be prepared)'}

═══════════════════════════════════════════════════════════════════
                        END OF HEARING BUNDLE
═══════════════════════════════════════════════════════════════════
`

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `Hearing_Bundle_${matterId}_${new Date().toISOString().split('T')[0]}.txt`
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
            <main className="flex-1 overflow-auto">
                {/* Formal Header */}
                <div className="border-b-2 border-[var(--border-primary)] bg-[var(--bg-secondary)] sticky top-0 z-10">
                    <div className="max-w-7xl mx-auto px-8 py-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <Gavel className="w-8 h-8 text-[var(--neon-purple)]" />
                                    <h1 className="text-3xl font-bold text-[var(--text-primary)]">HEARING BUNDLE PREPARATION</h1>
                                </div>
                                <div className="text-sm text-[var(--text-secondary)] font-mono">
                                    Matter Ref: <span className="text-[var(--neon-cyan)] font-semibold">{matterId}</span>
                                    {matterData?.title && <span className="ml-4">| {matterData.title}</span>}
                                </div>
                            </div>
                            <div className="text-right text-sm text-[var(--text-tertiary)]">
                                <div>Generated: {new Date().toLocaleDateString('en-MY', { day: '2-digit', month: 'long', year: 'numeric' })}</div>
                                <div className="text-xs mt-1" suppressHydrationWarning>{new Date().toLocaleTimeString('en-MY')}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-8 py-8">
                    <div className="grid lg:grid-cols-4 gap-8">
                        {/* Left Sidebar - Document Selection */}
                        <div className="lg:col-span-1 space-y-6">
                            <div className="card p-6">
                                <h2 className="text-base font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2 border-b border-[var(--border-primary)] pb-3">
                                    <FileText className="w-5 h-5 text-[var(--neon-cyan)]" />
                                    DOCUMENTS ({selectedDocs.length}/{documents?.length || 0})
                                </h2>

                                {docsLoading ? (
                                    <div className="flex justify-center py-8">
                                        <Loader2 className="w-8 h-8 animate-spin text-[var(--neon-cyan)]" />
                                    </div>
                                ) : documents && documents.length > 0 ? (
                                    <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                                        {documents.map((doc: any, idx: number) => (
                                            <label
                                                key={doc.id}
                                                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${selectedDocs.includes(doc.id)
                                                    ? 'border-[var(--neon-cyan)] bg-[var(--neon-cyan)]/10'
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
                                                    <div className="text-xs font-mono text-[var(--neon-orange)] mb-1">EXH-{String(idx + 1).padStart(3, '0')}</div>
                                                    <div className="font-medium text-sm text-[var(--text-primary)] truncate">{doc.filename}</div>
                                                    <div className="text-xs text-[var(--text-tertiary)] mt-1">{doc.mime_type}</div>
                                                </div>
                                            </label>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-[var(--text-tertiary)] text-sm text-center py-4">No documents available</p>
                                )}
                            </div>

                            {/* Action Buttons */}
                            <div className="space-y-3">
                                <button
                                    onClick={() => evidenceMutation.mutate()}
                                    disabled={selectedDocs.length === 0 || evidenceMutation.isPending}
                                    className="w-full btn-primary py-3 flex items-center justify-center gap-2 text-sm font-semibold"
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
                                    className="w-full px-6 py-3 bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-[var(--neon-purple)]/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
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
                                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                                    <div className="font-bold flex items-center gap-2 mb-1">
                                        <AlertCircle className="w-4 h-4" />
                                        Error
                                    </div>
                                    {evidenceMutation.error?.message || hearingMutation.error?.message || 'An error occurred'}
                                </div>
                            )}
                        </div>

                        {/* Main Content - Preview */}
                        <div className="lg:col-span-3">
                            {hearingMutation.data ? (
                                <div className="space-y-8">
                                    {/* Success Banner */}
                                    <div className="card p-6 bg-gradient-to-r from-[var(--neon-green)]/10 to-transparent border-l-4 border-[var(--neon-green)]">
                                        <div className="flex items-center justify-between flex-wrap gap-4">
                                            <div className="flex items-center gap-3">
                                                <CheckCircle2 className="w-6 h-6 text-[var(--neon-green)]" />
                                                <div>
                                                    <h3 className="font-bold text-[var(--neon-green)]">HEARING BUNDLE PREPARED</h3>
                                                    <p className="text-sm text-[var(--text-secondary)] mt-1">Bundle is ready for court submission</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {isSpeaking ? (
                                                    <button
                                                        onClick={stopSpeaking}
                                                        className="flex items-center gap-2 px-4 py-2 bg-[var(--neon-red)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                                                    >
                                                        <Square className="w-4 h-4" />
                                                        Stop Reading
                                                    </button>
                                                ) : (
                                                    <button
                                                        onClick={() => {
                                                            const script = hearingMutation.data?.hearing_bundle?.oral_script_ms
                                                                ? `Oral Submission Script. ${hearingMutation.data.hearing_bundle.oral_script_ms}. English Notes. ${hearingMutation.data.hearing_bundle.oral_script_en_notes || ''}`
                                                                : 'No script available to read.'

                                                            const utterance = new SpeechSynthesisUtterance(script)

                                                            // Voice Selection Logic - Prioritize Malaysian/Nusantara Female Voices
                                                            const voices = window.speechSynthesis.getVoices()

                                                            const malaysianVoice = voices.find(v =>
                                                                // Priority 1: Specific Malaysian Female Voices (Windows/Android)
                                                                v.name.includes('Yati') || // Microsoft Yati (common on Windows)
                                                                (v.lang === 'ms-MY' && v.name.includes('Female')) ||
                                                                (v.lang === 'en-MY' && v.name.includes('Female')) ||

                                                                // Priority 2: Any Malaysian/Indonesian Voice (Accents are similar)
                                                                v.lang === 'ms-MY' ||
                                                                v.lang === 'id-ID' || // Indonesian often sounds closer than Western accents
                                                                v.name.includes('Malay') ||
                                                                v.name.includes('Indo')
                                                            )

                                                            // Priority 3: General Female English if no Malaysian found
                                                            const fallbackFemale = voices.find(v =>
                                                                v.name.includes('Zira') ||
                                                                v.name.includes('Google US English') ||
                                                                v.name.includes('Samantha') ||
                                                                (v.name.includes('Female') && v.lang.startsWith('en'))
                                                            )

                                                            if (malaysianVoice) {
                                                                utterance.voice = malaysianVoice
                                                                // Malaysian English often sounds natural at slightly faster or standard rate
                                                                utterance.rate = 1.0
                                                                // Ensure we use the voice's language correct pronunciation if it's a Malay voice reading English/Malay mixed text
                                                                utterance.lang = malaysianVoice.lang
                                                            } else if (fallbackFemale) {
                                                                utterance.voice = fallbackFemale
                                                                utterance.pitch = 1.1
                                                                utterance.rate = 0.9
                                                            }

                                                            utterance.onend = () => {
                                                                setIsSpeaking(false)
                                                                setCurrentSection('')
                                                            }

                                                            setIsSpeaking(true)
                                                            setCurrentSection('Oral Submission')
                                                            window.speechSynthesis.speak(utterance)
                                                        }}
                                                        className="flex items-center gap-2 px-4 py-2 bg-[var(--neon-purple)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                                                    >
                                                        <Volume2 className="w-4 h-4" />
                                                        Read Aloud
                                                    </button>
                                                )}
                                                <button
                                                    onClick={downloadHearingBundlePDF}
                                                    className="flex items-center gap-2 px-4 py-2 bg-[var(--neon-blue)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                                                >
                                                    <Download className="w-4 h-4" />
                                                    Download
                                                </button>
                                                <button className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-[var(--border-primary)] rounded-lg text-sm font-medium hover:bg-[var(--bg-secondary)] transition-colors">
                                                    <Printer className="w-4 h-4" />
                                                    Print
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {isSpeaking && currentSection && (
                                        <div className="flex items-center gap-3 p-4 rounded-lg bg-[var(--neon-purple)]/10 border border-[var(--neon-purple)]/20">
                                            <div className="w-3 h-3 bg-[var(--neon-purple)] rounded-full animate-pulse"></div>
                                            <span className="text-[var(--neon-purple)] font-medium text-sm">Now reading: {currentSection}</span>
                                        </div>
                                    )}

                                    {/* Table of Contents */}
                                    <div className="card">
                                        <div className="border-b-2 border-[var(--border-primary)] p-6 bg-[var(--bg-secondary)]">
                                            <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                                                <BookOpen className="w-5 h-5 text-[var(--neon-orange)]" />
                                                TABLE OF CONTENTS
                                            </h2>
                                        </div>
                                        <div className="p-6">
                                            <div className="space-y-4">
                                                {hearingMutation.data.hearing_bundle?.tabs?.map((tab: any, idx: number) => (
                                                    <div key={idx} className="border-l-4 border-[var(--neon-cyan)] pl-4 py-2">
                                                        <div className="flex items-baseline gap-3">
                                                            <span className="font-mono font-bold text-[var(--neon-cyan)] text-lg">TAB {tab.tab}</span>
                                                            <span className="font-semibold text-[var(--text-primary)] uppercase tracking-wide">{tab.section}</span>
                                                        </div>
                                                        {tab.items?.length > 0 && (
                                                            <ul className="mt-3 space-y-2 ml-8">
                                                                {tab.items.map((item: any, i: number) => (
                                                                    <li key={i} className="flex items-start gap-3 text-sm">
                                                                        <span className="font-mono text-[var(--text-tertiary)] min-w-[2rem]">{i + 1}.</span>
                                                                        <div className="flex-1">
                                                                            <div className="text-[var(--text-secondary)]">{item.description}</div>
                                                                            <div className="text-xs text-[var(--text-tertiary)] mt-1">Language: {item.language} | Pages: {item.pages}</div>
                                                                        </div>
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Oral Submission Script */}
                                    <div className="card">
                                        <div className="border-b-2 border-[var(--border-primary)] p-6 bg-[var(--bg-secondary)]">
                                            <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                                                <Gavel className="w-5 h-5 text-[var(--neon-orange)]" />
                                                SKRIP HUJAHAN LISAN (BAHASA MALAYSIA)
                                            </h2>
                                            <p className="text-sm text-[var(--text-secondary)] mt-2">Oral Submission for Court Proceedings</p>
                                        </div>
                                        <div className="p-8 bg-gradient-to-br from-[var(--neon-orange)]/5 to-transparent">
                                            <div className="prose prose-invert max-w-none">
                                                {hearingMutation.data.hearing_bundle?.oral_script_ms?.split('\n\n').map((paragraph: string, idx: number) => (
                                                    <p key={idx} className="text-[var(--text-primary)] leading-relaxed mb-6 last:mb-0 text-justify font-serif text-base">
                                                        {paragraph}
                                                    </p>
                                                )) || <p className="text-[var(--text-tertiary)] italic text-center py-8">Script will be generated upon preparation</p>}
                                            </div>
                                        </div>
                                    </div>

                                    {/* English Notes */}
                                    <div className="card">
                                        <div className="border-b-2 border-[var(--border-primary)] p-6 bg-[var(--bg-secondary)]">
                                            <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                                                <FileCheck className="w-5 h-5 text-[var(--neon-cyan)]" />
                                                ENGLISH COMPANION NOTES
                                            </h2>
                                            <p className="text-sm text-[var(--text-secondary)] mt-2">Translation and Legal References</p>
                                        </div>
                                        <div className="p-8 bg-gradient-to-br from-[var(--neon-cyan)]/5 to-transparent">
                                            <div className="prose prose-invert max-w-none">
                                                {hearingMutation.data.hearing_bundle?.oral_script_en_notes?.split('\n\n').map((paragraph: string, idx: number) => {
                                                    // Check if paragraph is a heading (starts with **)
                                                    if (paragraph.startsWith('**') && paragraph.includes(':**')) {
                                                        return (
                                                            <h3 key={idx} className="text-[var(--neon-cyan)] font-bold text-lg mt-6 mb-3 first:mt-0">
                                                                {paragraph.replace(/\*\*/g, '').replace(':', '')}
                                                            </h3>
                                                        )
                                                    }
                                                    // Check if it's a list item
                                                    if (paragraph.trim().startsWith('-')) {
                                                        return (
                                                            <div key={idx} className="ml-4 mb-3">
                                                                <div className="flex gap-3">
                                                                    <span className="text-[var(--neon-orange)]">•</span>
                                                                    <p className="flex-1 text-[var(--text-secondary)] leading-relaxed">
                                                                        {paragraph.replace(/^-\s*/, '')}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                        )
                                                    }
                                                    return (
                                                        <p key={idx} className="text-[var(--text-secondary)] leading-relaxed mb-4 last:mb-0 text-justify">
                                                            {paragraph}
                                                        </p>
                                                    )
                                                }) || <p className="text-[var(--text-tertiary)] italic text-center py-8">Notes will be generated upon preparation</p>}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Q&A Section */}
                                    {hearingMutation.data.hearing_bundle?.if_judge_asks && hearingMutation.data.hearing_bundle.if_judge_asks.length > 0 && (
                                        <div className="card">
                                            <div className="border-b-2 border-[var(--border-primary)] p-6 bg-[var(--bg-secondary)]">
                                                <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                                                    <Sparkles className="w-5 h-5 text-[var(--neon-purple)]" />
                                                    ANTICIPATED JUDICIAL QUESTIONS
                                                </h2>
                                                <p className="text-sm text-[var(--text-secondary)] mt-2">Prepared Responses with Legal Authorities</p>
                                            </div>
                                            <div className="p-6">
                                                <div className="space-y-6">
                                                    {hearingMutation.data.hearing_bundle.if_judge_asks.map((qa: any, idx: number) => (
                                                        <div key={idx} className="border border-[var(--border-primary)] rounded-lg p-5 bg-[var(--bg-tertiary)] hover:border-[var(--neon-purple)]/30 transition-colors">
                                                            <div className="flex items-start gap-4">
                                                                <div className="font-mono font-bold text-[var(--neon-purple)] text-lg">{idx + 1}</div>
                                                                <div className="flex-1 space-y-3">
                                                                    <div>
                                                                        <div className="text-xs font-bold text-[var(--neon-orange)] uppercase tracking-wide mb-1">Question</div>
                                                                        <p className="text-[var(--text-primary)] font-medium">{qa.question}</p>
                                                                    </div>

                                                                    <div className="grid md:grid-cols-2 gap-4">
                                                                        <div className="space-y-2">
                                                                            <div className="text-xs font-bold text-[var(--neon-cyan)] uppercase tracking-wide">Answer (Malay)</div>
                                                                            <div className="p-4 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-primary)]">
                                                                                <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">{qa.answer_ms}</p>
                                                                            </div>
                                                                        </div>
                                                                        <div className="space-y-2">
                                                                            <div className="text-xs font-bold text-[var(--neon-cyan)] uppercase tracking-wide">Answer (English)</div>
                                                                            <div className="p-4 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-primary)]">
                                                                                <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">{qa.answer_en}</p>
                                                                            </div>
                                                                        </div>
                                                                    </div>

                                                                    <div className="flex items-center justify-between pt-2 border-t border-[var(--border-primary)]">
                                                                        <div className="text-xs">
                                                                            <span className="text-[var(--text-tertiary)]">Authority:</span>{' '}
                                                                            <span className="text-[var(--neon-green)] font-mono">{qa.authority}</span>
                                                                        </div>
                                                                        <div className="flex items-center gap-2">
                                                                            <div className="h-2 w-24 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                                                                                <div
                                                                                    className="h-full bg-gradient-to-r from-[var(--neon-orange)] to-[var(--neon-green)]"
                                                                                    style={{ width: `${(qa.confidence * 100).toFixed(0)}%` }}
                                                                                ></div>
                                                                            </div>
                                                                            <span className="text-xs font-mono text-[var(--neon-green)]">{(qa.confidence * 100).toFixed(0)}%</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : evidenceMutation.data ? (
                                // Evidence Packet View (unchanged)
                                <div className="card p-6">
                                    <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--neon-green)]/10 border border-[var(--neon-green)]/20 mb-6">
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
                                </div>
                            ) : (
                                <div className="card p-12 text-center">
                                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                                        <Scale className="w-10 h-10 text-[var(--text-tertiary)]" />
                                    </div>
                                    <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">No Bundle Prepared</h3>
                                    <p className="text-[var(--text-secondary)] max-w-md mx-auto">
                                        Select documents from the sidebar and click "Prepare Hearing Bundle" to generate your court-ready materials.
                                    </p>
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
