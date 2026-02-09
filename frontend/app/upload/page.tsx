'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { 
    Upload, 
    FileText, 
    Loader2, 
    Mail, 
    MessageCircle, 
    Database, 
    X, 
    Sparkles, 
    Zap, 
    Shield, 
    Clock,
    Inbox,
    Scale,
    Link2
} from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'
import { motion, AnimatePresence } from 'framer-motion'

export default function UploadPage() {
    const router = useRouter()
    const [files, setFiles] = useState<File[]>([])
    const [connectorType, setConnectorType] = useState('upload')
    const [dragActive, setDragActive] = useState(false)
    const [processingStep, setProcessingStep] = useState<string | null>(null)
    const [contextDetails, setContextDetails] = useState<string | null>(null)

    const uploadMutation = useMutation({
        onMutate: () => {
            setProcessingStep("Initializing Archival Engine...")
            setContextDetails("Calibrating legal neural nodes...")
        },
        mutationFn: async () => {
            const formData = new FormData()
            files.forEach((file) => {
                formData.append('files', file)
            })
            formData.append('connector_type', connectorType)
            formData.append('metadata', JSON.stringify({}))

            return api.startIntakeWorkflow(formData)
        },
        onSuccess: (data) => {
            if (data && data.matter_id && (data.status === 'success' || data.status === 'processing')) {
                if (data.status === 'processing' || data.workflow_status === 'processing') {
                    setProcessingStep("Analyzing Jurisprudential Texture...")
                    setContextDetails("This manuscript is being indexed into the heritage registry...")
                    pollForCompletion(data.matter_id)
                } else {
                    router.push(`/matter/${data.matter_id}`)
                }
            } else {
                alert('Intake started but registry ID was not received.')
            }
        },
        onError: (error: any) => {
            setProcessingStep(null)
            alert(`Archival Error: ${error.message || 'Unknown internal failure'}`)
        },
    })

    const pollForCompletion = async (matterId: string) => {
        const checkStatus = async () => {
            try {
                const matter = await api.getMatter(matterId)
                if (matter) {
                    if (matter.processing_status && matter.status !== 'failed') {
                        setProcessingStep(matter.processing_status)
                    }
                    if (matter.status === 'structured' || matter.status === 'active' || matter.status === 'ready') {
                        router.push(`/matter/${matterId}`)
                        return true
                    } else if (matter.status === 'failed') {
                        alert("Processing failed. Please try again.")
                        setProcessingStep(null)
                        return true
                    }
                }
            } catch (e) {
                console.error("Polling error:", e)
            }
            return false
        }

        const interval = setInterval(async () => {
            const done = await checkStatus()
            if (done) clearInterval(interval)
        }, 3000)
    }

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
        else if (e.type === 'dragleave') setDragActive(false)
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            setFiles((prev) => [...prev, ...Array.from(e.dataTransfer.files)])
        }
    }

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFiles((prev) => [...prev, ...Array.from(e.target.files!)])
        }
    }

    const removeFile = (index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index))
    }

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    const connectorOptions = [
        { value: 'upload', label: 'Manuscript Upload', icon: Upload },
        { value: 'gmail', label: 'Digital Dispatch (Mail)', icon: Mail },
        { value: 'whatsapp_export', label: 'Mobile Records', icon: MessageCircle },
        { value: 'dms', label: 'Central Archive Flow', icon: Database },
    ]

    const pipelineSteps = [
        { icon: FileText, text: 'Deduplication & Indexing' },
        { icon: Sparkles, text: 'Bilingual OCR Transcription' },
        { icon: Zap, text: 'Archival Synthesis' },
        { icon: Shield, text: 'Structured Registry Entry' },
        { icon: Clock, text: 'Merit Scoring & Risks' },
        { icon: Scale, text: 'Executive Summary Generation' },
    ]

    return (
        <div className="flex min-h-screen bg-[#0A0A0A] font-serif text-white selection:bg-[#D4A853]/30">
            <Sidebar />
            <main className="flex-1 p-8 lg:p-12 relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('/grain.png')] opacity-[0.03] pointer-events-none"></div>
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#D4A853] opacity-[0.02] blur-[150px] rounded-full pointer-events-none"></div>

                <header className="mb-12 relative z-10">
                    <div className="flex items-center gap-6">
                        <div className="w-16 h-16 bg-[#1A1A1A] border border-[#D4A853]/40 flex items-center justify-center shadow-2xl">
                            <Inbox className="w-8 h-8 text-[#D4A853]" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3 text-[#D4A853] text-xs font-bold tracking-[0.3em] uppercase mb-1">
                                <span className="w-8 h-[1px] bg-[#D4A853]"></span>
                                Registry Submission
                                <span className="w-8 h-[1px] bg-[#D4A853]"></span>
                            </div>
                            <h1 className="text-5xl font-black text-white tracking-tighter uppercase font-serif italic">
                                Archival <span className="text-[#D4A853] not-italic">Intake</span>
                            </h1>
                        </div>
                    </div>
                </header>

                <div className="max-w-5xl mx-auto grid lg:grid-cols-12 gap-10">
                    {/* Left: Input Selection */}
                    <div className="lg:col-span-8 space-y-8">
                        <section className="bg-[#141414] border border-[#D4A853]/10 p-8 shadow-2xl">
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-[#D4A853] mb-8 flex items-center gap-3 border-b border-[#D4A853]/10 pb-4">
                                <Link2 className="w-4 h-4" />
                                Source Protocol
                            </h2>
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                {connectorOptions.map((option) => (
                                    <button
                                        key={option.value}
                                        onClick={() => setConnectorType(option.value)}
                                        className={`p-6 border transition-all duration-500 flex flex-col items-center gap-4 ${
                                            connectorType === option.value
                                            ? 'bg-[#1A1A1A] border-[#D4A853] shadow-[0_0_30px_rgba(212,168,83,0.1)]'
                                            : 'bg-transparent border-[#D4A853]/05 hover:border-[#D4A853]/30 hover:bg-slate-900/05'
                                        }`}
                                    >
                                        <div className={`w-12 h-12 flex items-center justify-center transition-all ${connectorType === option.value ? 'text-[#D4A853]' : 'text-slate-400'}`}>
                                            <option.icon className="w-8 h-8" />
                                        </div>
                                        <div className={`text-[10px] font-black uppercase tracking-widest text-center leading-tight ${connectorType === option.value ? 'text-white' : 'text-gray-500'}`}>
                                            {option.label}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </section>

                        <section className="bg-[#141414] border border-[#D4A853]/10 p-8 shadow-2xl">
                             <h2 className="text-xs font-black uppercase tracking-[0.2em] text-[#D4A853] mb-8 flex items-center gap-3 border-b border-[#D4A853]/10 pb-4">
                                <FileText className="w-4 h-4" />
                                Document Depository
                            </h2>

                            <div
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                                className={`relative border border-dashed p-16 text-center transition-all duration-500 ${
                                    dragActive ? 'border-[#D4A853] bg-[#D4A853]/05' : 'border-[#D4A853]/20 hover:border-[#D4A853]/50 bg-black/20'
                                }`}
                            >
                                <div className="relative z-10 flex flex-col items-center">
                                    <div className="w-20 h-20 mb-6 bg-black border border-[#D4A853]/30 flex items-center justify-center shadow-inner">
                                        <Upload className={`w-10 h-10 transition-all ${dragActive ? 'text-[#D4A853] scale-110' : 'text-slate-400'}`} />
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-2 uppercase tracking-wide">Relinquish Manuscripts Here</h3>
                                    <p className="text-gray-500 text-sm italic font-serif opacity-70 mb-8">PDF, Word, Images, or Text files formats are accepted.</p>
                                    
                                    <input type="file" multiple onChange={handleFileInput} className="hidden" id="file-upload" accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png" />
                                    <label
                                        htmlFor="file-upload"
                                        className="cursor-pointer px-10 py-4 bg-[#D4A853] hover:bg-[#B88A3E] text-white font-black uppercase tracking-widest transition-all duration-300 shadow-xl"
                                    >
                                        Browse Archive
                                    </label>
                                </div>
                            </div>

                            <AnimatePresence>
                                {files.length > 0 && (
                                    <motion.div 
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        className="mt-10 space-y-4"
                                    >
                                        <div className="flex items-center justify-between text-[#D4A853] text-[10px] font-black uppercase tracking-[0.3em]">
                                            <span>Queued for Processing</span>
                                            <span className="bg-[#D4A853]/10 px-2 py-0.5 border border-[#D4A853]/20">{files.length} ITEMS</span>
                                        </div>
                                        <div className="space-y-3 max-h-64 overflow-y-auto pr-3 custom-scrollbar">
                                            {files.map((file, index) => (
                                                <div key={index} className="flex items-center justify-between p-4 bg-black/40 border border-[#D4A853]/05 group">
                                                    <div className="flex items-center gap-4">
                                                        <FileText className="w-5 h-5 text-[#D4A853]/50" />
                                                        <div>
                                                            <div className="text-sm font-bold text-white uppercase tracking-tight">{file.name}</div>
                                                            <div className="text-[10px] text-gray-500 font-bold">{formatFileSize(file.size)}</div>
                                                        </div>
                                                    </div>
                                                    <button onClick={() => removeFile(index)} className="text-slate-400 hover:text-red-500 transition-colors">
                                                        <X className="w-5 h-5" />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </section>
                    </div>

                    {/* Right: Info & Action */}
                    <div className="lg:col-span-4 space-y-8">
                        <section className="bg-[#141414] border border-[#D4A853]/10 p-8 shadow-2xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-[#D4A853]/05 blur-3xl rounded-full"></div>
                            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[#D4A853] mb-8 flex items-center gap-3 border-b border-[#D4A853]/10 pb-4">
                                <Zap className="w-4 h-4" />
                                Synthesis Pipeline
                            </h3>
                            <div className="space-y-6">
                                {pipelineSteps.map((step, index) => (
                                    <div key={index} className="flex items-start gap-4">
                                        <div className="mt-1 w-6 h-6 border-[0.5px] border-[#D4A853]/30 flex items-center justify-center bg-black/40">
                                            <step.icon className="w-3 h-3 text-[#D4A853]" />
                                        </div>
                                        <div className="text-xs font-bold text-gray-400 uppercase tracking-widest leading-loose">
                                            {step.text}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <button
                            onClick={() => uploadMutation.mutate()}
                            disabled={files.length === 0 || uploadMutation.isPending}
                            className="w-full py-6 bg-[#D4A853] hover:bg-[#B88A3E] text-white font-black uppercase tracking-[0.3em] transition-all duration-500 shadow-[0_20px_40px_rgba(0,0,0,0.3)] disabled:opacity-20 disabled:grayscale"
                        >
                            {uploadMutation.isPending ? (
                                <div className="flex items-center justify-center gap-4">
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                    <span>Processing...</span>
                                </div>
                            ) : (
                                <span>Authorize Analysis</span>
                            )}
                        </button>
                    </div>
                </div>

                {/* Processing Overlay */}
                <AnimatePresence>
                    {processingStep && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-[#0A0A0A]/95 backdrop-blur-xl z-50 flex items-center justify-center p-8"
                        >
                            <div className="max-w-xl w-full text-center space-y-12">
                                <div className="relative inline-block">
                                    <div className="absolute inset-[-40px] border border-[#D4A853]/10 animate-spin-slow"></div>
                                    <div className="absolute inset-[-60px] border border-[#D4A853]/05 animate-spin-reverse-slow"></div>
                                    <div className="w-32 h-32 bg-black border border-[#D4A853]/40 flex items-center justify-center shadow-[0_0_60px_rgba(212,168,83,0.1)]">
                                        <Loader2 className="w-12 h-12 text-[#D4A853] animate-spin" />
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <h3 className="text-4xl font-black text-white uppercase tracking-tighter font-serif italic">{processingStep}</h3>
                                    {contextDetails && (
                                        <p className="text-[#D4A853]/60 italic font-serif text-lg">{contextDetails}</p>
                                    )}
                                </div>

                                <div className="relative w-full h-[1px] bg-gray-900 overflow-hidden">
                                    <motion.div 
                                        initial={{ left: '-100%' }}
                                        animate={{ left: '100%' }}
                                        transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
                                        className="absolute top-0 bottom-0 w-1/3 bg-gradient-to-r from-transparent via-[#D4A853] to-transparent shadow-[0_0_20px_rgba(212,168,83,0.5)]"
                                    />
                                </div>
                                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.5em]">The archives are being meticulously transcribed</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>
        </div>
    )
}
