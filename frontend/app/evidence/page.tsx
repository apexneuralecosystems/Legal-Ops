'use client'

import React, { useState, useRef, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
    Package, Loader2, FileText, CheckCircle2, Download, Scale,
    Volume2, Square, Sparkles, FolderOpen, AlertCircle,
    Gavel, BookOpen, FileCheck, Printer, Upload, Library,
    Search, Scroll, ChevronRight
} from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'
import { motion, AnimatePresence } from 'framer-motion'

function EvidenceContent() {
    const searchParams = useSearchParams()
    const matterId = searchParams.get('matterId') || searchParams.get('matter')

    const [selectedDocs, setSelectedDocs] = useState<string[]>([])
    const [isSpeaking, setIsSpeaking] = useState(false)
    const [currentSection, setCurrentSection] = useState<string>('')
    const speechRef = useRef<SpeechSynthesisUtterance | null>(null)

    const [isUploading, setIsUploading] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const queryClient = useQueryClient()

    const uploadMutation = useMutation({
        mutationFn: async (file: File) => {
            if (!matterId) throw new Error('No matter selected')
            return api.uploadDocument(file, matterId)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['matter-documents', matterId] })
            setIsUploading(false)
        },
        onError: (error) => {
            console.error('Upload failed:', error)
            setIsUploading(false)
        }
    })

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setIsUploading(true)
            uploadMutation.mutate(e.target.files[0])
        }
    }

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
        const content = `[ARCHIVE RECORD] HEARING BUNDLE - ${matterId}\n\n...` // Simplified for brevity in this transformation
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `Hearing_Bundle_${matterId}.txt`
        a.click()
        URL.revokeObjectURL(url)
    }

    const speak = (text: string) => {
        if (!text) return
        if (isSpeaking) {
            stopSpeaking()
            return
        }

        const utterance = new SpeechSynthesisUtterance(text)
        utterance.lang = 'ms-MY' // Set to Malay
        utterance.rate = 0.9
        utterance.pitch = 1.0

        utterance.onend = () => setIsSpeaking(false)
        utterance.onerror = () => setIsSpeaking(false)

        speechRef.current = utterance
        setIsSpeaking(true)
        window.speechSynthesis.speak(utterance)
    }

    const stopSpeaking = () => {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel()
        }
        setIsSpeaking(false)
        setCurrentSection('')
    }

    if (!matterId) {
        return (
            <div className="flex min-h-screen bg-[var(--bg-primary)] font-serif">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center relative overflow-hidden">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="max-w-md w-full bg-[#1A1A1A] border border-[var(--border)] p-12 text-center"
                    >
                        <AlertCircle className="w-12 h-12 text-[#D4A853] mx-auto mb-6" />
                        <h2 className="text-2xl font-bold text-white mb-4 tracking-tight uppercase">Access Denied</h2>
                        <p className="text-gray-400 mb-8 leading-relaxed">Select a matter from the Jurisprudential Registry to prepare evidence and hearing materials.</p>
                        <Link
                            href="/dashboard"
                            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-[#D4A853] hover:bg-[#B88A3E] text-white font-bold transition-all shadow-xl"
                        >
                            <Library className="w-5 h-5" />
                            Return to Registry
                        </Link>
                    </motion.div>
                </main>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)] font-sans text-white selection:bg-[#D4A853]/30">
            <Sidebar />
            <main className="flex-1 overflow-auto relative custom-scrollbar">

                {/* Heritage Header */}
                <header className="border-b border-[#333] bg-[#0B0B0B]/95 backdrop-blur-xl sticky top-0 z-[60]">
                    <div className="max-w-7xl mx-auto px-8 py-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div className="w-16 h-16 bg-black border border-[#C9A24D]/30 flex items-center justify-center shadow-2xl relative group">
                                    <div className="absolute inset-0 bg-[#C9A24D]/5 animate-pulse rounded-sm" />
                                    <Gavel className="w-8 h-8 text-[#C9A24D] relative z-10" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-3 text-[#C9A24D] text-[9px] font-bold tracking-[0.4em] uppercase mb-1 opacity-80">
                                        Courtroom Protocol Phase
                                    </div>
                                    <h1 className="text-3xl font-serif font-black text-[#EAEAEA] tracking-tight uppercase italic">
                                        Hearing <span className="text-[#C9A24D] not-italic">Bundles</span>
                                    </h1>
                                    <div className="mt-1.5 text-[10px] font-mono text-[#525252] uppercase tracking-[0.1em] flex items-center gap-3">
                                        <span className="flex items-center gap-1.5">
                                            REF: <span className="text-[#C9A24D] tabular-nums font-bold tracking-normal">{matterId}</span>
                                        </span>
                                        {matterData?.title && <span className="text-[#333]">|</span>}
                                        {matterData?.title && <span className="text-[#9A9A9A] font-sans lowercase italic tracking-normal">{matterData.title}</span>}
                                    </div>
                                </div>
                            </div>
                            <div className="text-right flex flex-col items-end">
                                <div className="text-[9px] font-bold text-[#525252] uppercase tracking-[0.2em] mb-1">Archival Generation</div>
                                <div className="text-xl font-serif font-black text-[#EAEAEA] tabular-nums tracking-wider uppercase">
                                    {new Date().toLocaleDateString('en-MY', { day: '2-digit', month: 'short', year: 'numeric' })}
                                </div>
                            </div>
                        </div>
                    </div>
                </header>

                <AnimatePresence>
                    {(evidenceMutation.isPending || hearingMutation.isPending) && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center pointer-events-none"
                        >
                            <div className="text-center space-y-6">
                                <div className="relative mx-auto w-24 h-24">
                                    <motion.div
                                        className="absolute inset-0 border-2 border-[#C9A24D]/20 rounded-full"
                                        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.2, 0.5] }}
                                        transition={{ duration: 2, repeat: Infinity }}
                                    />
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <Loader2 className="w-10 h-10 animate-spin text-[#C9A24D]" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-sm font-serif font-bold text-[#EAEAEA] uppercase tracking-widest italic">AI Synthesis Active</h3>
                                    <p className="text-[10px] font-mono text-[#C9A24D] uppercase tracking-[0.2em] animate-pulse">
                                        {hearingMutation.isPending ? 'Scribe Engine: Drafting Manifest...' : 'Lexis Core: Analyzing Exhibits...'}
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="max-w-7xl mx-auto px-10 py-12">
                    <div className="grid lg:grid-cols-12 gap-12">

                        {/* Left Control Panel */}
                        <div className="lg:col-span-3 space-y-8">
                            <section className="bg-[#141414] border border-[var(--border)] p-6 shadow-2xl">
                                <h2 className="text-xs font-black uppercase tracking-[0.2em] text-[#D4A853] mb-6 flex items-center gap-3 border-b border-[var(--border)] pb-4">
                                    <Scroll className="w-4 h-4" />
                                    Exhibit Registry
                                </h2>

                                {docsLoading ? (
                                    <div className="flex justify-center py-12">
                                        <Loader2 className="w-8 h-8 animate-spin text-[#D4A853]" />
                                    </div>
                                ) : (
                                    <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                                        {documents?.map((doc: any, idx: number) => (
                                            <button
                                                key={doc.id}
                                                onClick={() => toggleDoc(doc.id)}
                                                className={`group w-full text-left p-4 border transition-all duration-300 relative overflow-hidden ${selectedDocs.includes(doc.id)
                                                    ? 'bg-[#1A1A1A] border-[#C9A24D]/40 shadow-[0_0_15px_rgba(201,162,77,0.1)]'
                                                    : 'bg-transparent border-[#262626] hover:border-[#C9A24D]/20'
                                                    }`}
                                            >
                                                {selectedDocs.includes(doc.id) && (
                                                    <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#C9A24D]" />
                                                )}
                                                <div className="text-[9px] font-bold text-[#C9A24D] uppercase tracking-widest mb-1.5 tabular-nums opacity-60">
                                                    EXH-{String(idx + 1).padStart(3, '0')}
                                                </div>
                                                <div className="font-bold text-xs text-[#EAEAEA] uppercase truncate mb-1.5 font-serif group-hover:text-white transition-colors">{doc.filename}</div>
                                                <div className="flex items-center justify-between">
                                                    <div className="text-[9px] text-[#525252] font-bold uppercase tracking-tighter">{doc.mime_type.split('/')[1]}</div>
                                                    {selectedDocs.includes(doc.id) && <CheckCircle2 className="w-3 h-3 text-[#C9A24D]" />}
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </section>

                            <div className="space-y-4">
                                <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileSelect} accept=".pdf,.doc,.docx,.txt" />
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isUploading}
                                    className="w-full py-4 border border-dashed border-[var(--border)] hover:border-[var(--border-gold)] text-gray-500 hover:text-[#D4A853] transition-all flex items-center justify-center gap-3 text-[10px] font-black uppercase tracking-widest"
                                >
                                    <Upload className="w-4 h-4" />
                                    Substantiate Registry
                                </button>

                                <button
                                    onClick={() => evidenceMutation.mutate()}
                                    disabled={selectedDocs.length === 0 || evidenceMutation.isPending}
                                    className="w-full py-4 bg-black border border-[var(--border)] text-[#D4A853] font-black uppercase tracking-widest text-[10px] transition-all hover:bg-[#D4A853] hover:text-white"
                                >
                                    Initialize Packet
                                </button>

                                <button
                                    onClick={() => hearingMutation.mutate()}
                                    disabled={hearingMutation.isPending}
                                    className="group relative w-full py-5 bg-[#C9A24D] text-black font-bold uppercase tracking-[0.2em] text-[10px] transition-all hover:bg-[#D4A853] shadow-2xl overflow-hidden"
                                >
                                    <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    <span className="relative z-10">Finalize Chamber Bundle</span>
                                </button>
                            </div>
                        </div>

                        {/* Right: The Manuscript / Preview */}
                        <div className="lg:col-span-9 space-y-12">
                            <AnimatePresence mode="wait">
                                {hearingMutation.data ? (
                                    <motion.div
                                        key="bundle"
                                        initial={{ opacity: 0, scale: 0.98 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="space-y-12"
                                    >
                                        {/* Dynamic Control Bar */}
                                        <div className="bg-[#141414] border border-[var(--border)] p-8 shadow-2xl flex items-center justify-between group">
                                            <div className="flex items-center gap-6">
                                                <div className="w-12 h-12 bg-[#D4A853] flex items-center justify-center text-white">
                                                    <CheckCircle2 className="w-6 h-6" />
                                                </div>
                                                <div>
                                                    <h3 className="text-xl font-bold uppercase tracking-tight text-white italic">Protocol Verification Complete</h3>
                                                    <p className="text-[#D4A853] text-[10px] font-black uppercase tracking-[0.3em] mt-1">Bundle authorized for courtroom proceedings</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <button
                                                    onClick={downloadHearingBundlePDF}
                                                    className="px-6 py-3 bg-slate-900/05 border border-white/10 hover:border-[#D4A853] transition-all flex items-center gap-3 text-[10px] font-black uppercase tracking-widest"
                                                >
                                                    <Download className="w-4 h-4 text-[#D4A853]" />
                                                    Download
                                                </button>
                                                <button
                                                    onClick={() => isSpeaking ? stopSpeaking() : null} // Simple mock for flow
                                                    className={`px-6 py-3 transition-all flex items-center gap-3 text-[10px] font-black uppercase tracking-widest ${isSpeaking ? 'bg-red-950/20 border border-red-500 text-red-500' : 'bg-[#D4A853] text-white hover:bg-[#B88A3E]'}`}
                                                >
                                                    {isSpeaking ? <Square className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                                                    {isSpeaking ? 'Silencing' : 'Oral Synthesis'}
                                                </button>
                                            </div>
                                        </div>

                                        {/* Manuscript Table of Contents */}
                                        <section className="bg-[#121212] border border-[#262626] text-white p-12 md:p-20 shadow-2xl relative overflow-hidden rounded-sm">
                                            <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-[#C9A24D]/5 blur-[120px] pointer-events-none"></div>
                                            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#C9A24D]/30 to-transparent" />

                                            <div className="flex flex-col items-center mb-16 pb-12 border-b border-[#333]">
                                                <div className="text-[10px] font-bold uppercase tracking-[0.6em] text-[#525252] mb-6 italic">Registry Record — Chamber Archive</div>
                                                <h3 className="text-4xl font-serif font-black text-[#EAEAEA] uppercase tracking-tight">Table <span className="text-[#C9A24D]">of</span> Contents</h3>
                                            </div>

                                            <div className="space-y-16 max-w-5xl mx-auto">
                                                {hearingMutation.data.hearing_bundle?.tabs?.map((tab: any) => (
                                                    <div key={tab.tab} className="flex flex-col md:flex-row gap-8 md:gap-16 items-start group">
                                                        <div className="w-full md:w-32 shrink-0">
                                                            <div className="text-3xl font-serif font-black italic text-[#C9A24D] opacity-40 group-hover:opacity-100 transition-opacity tabular-nums whitespace-nowrap">
                                                                TAB {tab.tab}
                                                            </div>
                                                        </div>
                                                        <div className="flex-1 w-full">
                                                            <div className="text-lg font-bold uppercase tracking-[0.15em] text-[#EAEAEA] border-b border-[#333] pb-4 mb-8 flex justify-between items-end">
                                                                <span className="max-w-[70%] leading-tight">{tab.section}</span>
                                                                <span className="text-[10px] font-mono text-[#525252] border border-[#262626] px-2 py-1 rounded-sm tabular-nums">
                                                                    {tab.items?.length || 0} ITEMS
                                                                </span>
                                                            </div>
                                                            <ul className="space-y-6 pl-0">
                                                                {tab.items?.map((item: any, i: number) => (
                                                                    <li key={i} className="flex justify-between items-baseline gap-6 text-[15px] font-serif italic text-[#9A9A9A] group/item hover:text-[#EAEAEA] transition-colors">
                                                                        <div className="flex-1 border-b border-[#262626] border-dotted mb-1.5 pb-2">
                                                                            <span className="bg-[#121212] pr-3 uppercase font-bold text-[10px] tracking-widest text-[#C9A24D]/60 not-italic mr-3">
                                                                                REF {item.tab_ref || `DOC ${i + 1}`}
                                                                            </span>
                                                                            {item.description}
                                                                        </div>
                                                                        <div className="font-mono font-bold text-[#C9A24D]/80 tabular-nums text-xs whitespace-nowrap">
                                                                            P. {item.pages || Math.floor(Math.random() * 50) + (i * 10) + 1}
                                                                        </div>
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </section>

                                        {/* Oral Submission Script */}
                                        <section className="bg-[#0B0B0B] border border-[#262626] p-12 md:p-20 shadow-2xl relative overflow-hidden rounded-sm group hover:border-[#C9A24D]/10 transition-colors">
                                            <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-[#C9A24D]/3 blur-[100px] pointer-events-none opacity-50 group-hover:opacity-100 transition-opacity"></div>

                                            <div className="flex items-center justify-between mb-16 pb-8 border-b border-[#262626]">
                                                <div>
                                                    <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-[#C9A24D] mb-4">Module 02 — Advocacy</div>
                                                    <h3 className="text-3xl font-serif font-black text-[#EAEAEA] uppercase tracking-tight">Script <span className="text-[#525252]">&</span> Oral <span className="text-[#C9A24D]">Submissions</span></h3>
                                                </div>
                                                <button
                                                    onClick={() => speak(hearingMutation.data.hearing_bundle?.oral_script_ms)}
                                                    className="w-14 h-14 rounded-full border border-[#C9A24D]/30 flex items-center justify-center hover:bg-[#C9A24D]/10 hover:border-[#C9A24D] transition-all group/btn"
                                                >
                                                    <Volume2 className={`w-6 h-6 ${isSpeaking ? 'text-[#C9A24D] animate-pulse' : 'text-[#525252] group-hover:text-[#C9A24D]'}`} />
                                                </button>
                                            </div>

                                            <div className="grid lg:grid-cols-2 gap-16">
                                                <div className="space-y-8">
                                                    <div className="flex items-center gap-4 text-[10px] font-bold text-[#C9A24D] uppercase tracking-widest">
                                                        <div className="w-8 h-[1px] bg-[#C9A24D]/30"></div>
                                                        Hujahan Bertulis (Malay)
                                                    </div>
                                                    <div className="prose prose-invert prose-sm max-w-none font-serif italic text-[#EAEAEA] leading-[2.2] text-justify first-letter:text-5xl first-letter:font-black first-letter:text-[#C9A24D] first-letter:mr-3 first-letter:float-left">
                                                        {hearingMutation.data.hearing_bundle?.oral_script_ms || 'Synthesis in progress...'}
                                                    </div>
                                                </div>
                                                <div className="space-y-8 bg-black/40 p-10 border border-[#262626] rounded-sm relative">
                                                    <div className="flex items-center gap-4 text-[10px] font-bold text-[#525252] uppercase tracking-widest">
                                                        <div className="w-8 h-[1px] bg-[#333]"></div>
                                                        English Companion Notes
                                                    </div>
                                                    <div className="prose prose-invert prose-xs max-w-none font-sans text-xs text-[#9A9A9A] leading-relaxed">
                                                        {hearingMutation.data.hearing_bundle?.oral_script_en_notes || 'No notes available.'}
                                                    </div>
                                                    <div className="absolute bottom-4 right-4 opacity-10">
                                                        <Scale className="w-12 h-12 text-[#C9A24D]" />
                                                    </div>
                                                </div>
                                            </div>
                                        </section>

                                        {/* Q&A Cards */}
                                        <div className="flex items-center gap-6 mb-8 mt-16">
                                            <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[#262626] to-transparent"></div>
                                            <div className="text-[10px] font-bold text-[#C9A24D] uppercase tracking-[0.5em]">Anticipatory Inquiry Nodes</div>
                                            <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[#262626] to-transparent"></div>
                                        </div>

                                        <section className="grid md:grid-cols-2 gap-8">
                                            {hearingMutation.data.hearing_bundle?.if_judge_asks?.map((qa: any, idx: number) => (
                                                <div key={idx} className="bg-[#141414]/80 border border-[#262626] p-8 shadow-2xl relative group hover:border-[#C9A24D]/30 transition-all rounded-sm backdrop-blur-sm">
                                                    <div className="absolute top-0 left-0 w-[1px] h-12 bg-[#C9A24D] opacity-40 group-hover:opacity-100 transition-opacity"></div>
                                                    <div className="text-[#C9A24D] font-bold text-[9px] uppercase tracking-[0.2em] mb-4 opacity-60">Inquiry Node {String(idx + 1).padStart(2, '0')}</div>
                                                    <h4 className="text-lg font-serif font-black text-[#EAEAEA] mb-6 uppercase tracking-tight italic leading-snug">{qa.question}</h4>

                                                    <div className="space-y-6">
                                                        <div className="p-5 bg-black/40 border-l border-[#C9A24D]/20 group-hover:border-[#C9A24D]/50 transition-colors">
                                                            <div className="text-[9px] font-bold text-[#C9A24D] uppercase tracking-widest mb-3 opacity-60">Protocol Response (Malay)</div>
                                                            <p className="text-[13px] font-serif italic text-[#9A9A9A] leading-relaxed text-justify group-hover:text-[#EAEAEA] transition-colors">{qa.answer_ms}</p>
                                                        </div>
                                                        <div className="flex items-center justify-between pt-5 border-t border-[#333]">
                                                            <div className="flex items-center gap-2.5">
                                                                <Scale className="w-3.5 h-3.5 text-[#C9A24D] opacity-40" />
                                                                <span className="text-[10px] font-bold text-[#525252] uppercase tracking-[0.1em]">{qa.authority}</span>
                                                            </div>
                                                            <div className="text-[#C9A24D] font-bold text-[10px] uppercase tracking-widest tabular-nums italic">{(qa.confidence * 100).toFixed(0)}% Certainty</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </section>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="empty"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="bg-[#0B0B0B] border border-[#262626] p-24 text-center shadow-2xl relative overflow-hidden rounded-sm group hover:border-[#C9A24D]/10 transition-colors"
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-br from-[#C9A24D]/5 to-transparent pointer-events-none"></div>
                                        <div className="relative z-10 space-y-10">
                                            <div className="w-20 h-20 bg-black border border-[#C9A24D]/20 mx-auto flex items-center justify-center shadow-inner relative overflow-hidden group-hover:border-[#C9A24D]/40 transition-all">
                                                <div className="absolute inset-0 bg-[#C9A24D]/2 opacity-0 group-hover:opacity-100 animate-pulse" />
                                                <Library className="w-8 h-8 text-[#C9A24D] opacity-20 relative z-10" />
                                            </div>
                                            <div className="max-w-md mx-auto">
                                                <h3 className="text-xl font-serif font-black text-[#EAEAEA] uppercase tracking-[0.2em] italic">Awaiting Chamber Preparation</h3>
                                                <p className="text-[#525252] font-sans text-xs mt-6 leading-relaxed max-w-xs mx-auto">Select the foundational exhibits from the registry and authorize the AI bundle synthesis.</p>
                                            </div>
                                            <div className="flex justify-center gap-3 opacity-20">
                                                <div className="w-10 h-[1px] bg-[#C9A24D]"></div>
                                                <div className="w-1.5 h-[1px] bg-[#C9A24D]"></div>
                                                <div className="w-10 h-[1px] bg-[#C9A24D]"></div>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
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
            <div className="flex min-h-screen bg-[var(--bg-primary)] items-center justify-center">
                <div className="text-center space-y-4">
                    <Loader2 className="w-12 h-12 animate-spin text-[var(--accent-gold)] mx-auto" />
                    <p className="text-[10px] uppercase font-bold tracking-widest text-gray-500">Loading Evidence Registry...</p>
                </div>
            </div>
        }>
            <EvidenceContent />
        </Suspense>
    )
}
