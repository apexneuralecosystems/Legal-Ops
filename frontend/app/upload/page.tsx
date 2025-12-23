'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { Upload, FileText, Loader2, Mail, MessageCircle, Database, X, Sparkles, Zap, Shield, Clock } from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'

export default function UploadPage() {
    const router = useRouter()
    const [files, setFiles] = useState<File[]>([])
    const [connectorType, setConnectorType] = useState('upload')
    const [dragActive, setDragActive] = useState(false)

    const uploadMutation = useMutation({
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
            console.log('Intake workflow started successfully:', data)
            router.push(`/matter/${data.matter_id}`)
        },
        onError: (error: any) => {
            console.error('Intake workflow failed:', error)
            alert(`Error starting intake workflow: ${error.message || 'Unknown error'}`)
        },
    })

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true)
        } else if (e.type === 'dragleave') {
            setDragActive(false)
        }
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const newFiles = Array.from(e.dataTransfer.files)
            setFiles((prev) => [...prev, ...newFiles])
        }
    }

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const newFiles = Array.from(e.target.files)
            setFiles((prev) => [...prev, ...newFiles])
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
        { value: 'upload', label: 'File Upload', icon: Upload, gradient: 'from-[var(--neon-purple)] to-[var(--neon-blue)]' },
        { value: 'gmail', label: 'Gmail', icon: Mail, gradient: 'from-[var(--neon-red)] to-[var(--neon-orange)]' },
        { value: 'whatsapp_export', label: 'WhatsApp', icon: MessageCircle, gradient: 'from-[var(--neon-green)] to-[var(--neon-cyan)]' },
        { value: 'dms', label: 'DMS', icon: Database, gradient: 'from-[var(--neon-pink)] to-[var(--neon-purple)]' },
    ]

    const workflowSteps = [
        { icon: FileText, text: 'Documents are collected and deduplicated' },
        { icon: Sparkles, text: 'OCR extracts text and detects language (Malay/English)' },
        { icon: Zap, text: 'Parallel translations are created' },
        { icon: Shield, text: 'Case details are structured (parties, court, dates, issues)' },
        { icon: Clock, text: 'Risk scores are calculated' },
        { icon: Sparkles, text: 'Matter Card is created on dashboard' },
    ]

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />
            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-cyan)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--neon-purple)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>
                
                <div className="mb-10 animate-fade-in">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="icon-box w-12 h-12">
                            <Upload className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold gradient-text">Matter Intake</h1>
                            <p className="text-[var(--text-secondary)] mt-1">Upload documents to initiate AI-powered case analysis</p>
                        </div>
                    </div>
                    <div className="cyber-line mt-6"></div>
                </div>

                <div className="max-w-4xl mx-auto space-y-8">
                    <div className="card p-6 animate-slide-up">
                        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
                            <Database className="w-5 h-5 text-[var(--neon-cyan)]" />
                            Source Type
                        </h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {connectorOptions.map((option) => (
                                <button
                                    key={option.value}
                                    onClick={() => setConnectorType(option.value)}
                                    className={`group relative p-5 rounded-xl border-2 transition-all duration-300 ${
                                        connectorType === option.value
                                            ? 'border-[var(--neon-purple)] bg-[var(--bg-secondary)]'
                                            : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                    }`}
                                >
                                    {connectorType === option.value && (
                                        <div className="absolute inset-0 bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-cyan)] opacity-10 rounded-xl"></div>
                                    )}
                                    <div className={`w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br ${option.gradient} flex items-center justify-center shadow-lg transition-transform duration-300 group-hover:scale-110`}>
                                        <option.icon className="w-6 h-6 text-white" />
                                    </div>
                                    <div className={`text-sm font-semibold ${connectorType === option.value ? 'text-[var(--neon-cyan)]' : 'text-[var(--text-secondary)]'}`}>
                                        {option.label}
                                    </div>
                                    {connectorType === option.value && (
                                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-[var(--neon-green)] rounded-full flex items-center justify-center">
                                            <div className="w-2 h-2 bg-white rounded-full"></div>
                                        </div>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="card p-6 animate-slide-up stagger-1">
                        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
                            <FileText className="w-5 h-5 text-[var(--neon-purple)]" />
                            Documents
                        </h2>

                        <div
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                            className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
                                dragActive
                                    ? 'border-[var(--neon-cyan)] bg-[var(--neon-cyan)]/5'
                                    : 'border-[var(--border-secondary)] hover:border-[var(--neon-purple)]/50 bg-[var(--bg-tertiary)]'
                            }`}
                        >
                            {dragActive && (
                                <div className="absolute inset-0 bg-gradient-to-br from-[var(--neon-cyan)]/10 to-[var(--neon-purple)]/10 rounded-2xl"></div>
                            )}
                            <div className="relative z-10">
                                <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-cyan)] flex items-center justify-center shadow-lg animate-float">
                                    <Upload className="w-10 h-10 text-white" />
                                </div>
                                <p className="text-xl font-semibold text-[var(--text-primary)] mb-2">
                                    Drag and drop files here
                                </p>
                                <p className="text-sm text-[var(--text-tertiary)] mb-6">
                                    PDF, Word, Images, Text files supported
                                </p>
                                <input
                                    type="file"
                                    multiple
                                    onChange={handleFileInput}
                                    className="hidden"
                                    id="file-upload"
                                    accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                                />
                                <label
                                    htmlFor="file-upload"
                                    className="btn-primary inline-flex items-center gap-2 px-8 py-3 cursor-pointer"
                                >
                                    <Sparkles className="w-5 h-5" />
                                    Browse Files
                                </label>
                            </div>
                        </div>

                        {files.length > 0 && (
                            <div className="mt-6 space-y-3">
                                <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-3 flex items-center gap-2">
                                    <span className="w-6 h-6 rounded-full bg-[var(--neon-purple)] flex items-center justify-center text-xs text-white">
                                        {files.length}
                                    </span>
                                    Selected Files
                                </h3>
                                <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
                                    {files.map((file, index) => (
                                        <div
                                            key={index}
                                            className="group flex items-center justify-between p-4 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-primary)] hover:border-[var(--neon-cyan)]/30 transition-all duration-300"
                                        >
                                            <div className="flex items-center gap-4 flex-1">
                                                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[var(--neon-blue)] to-[var(--neon-purple)] flex items-center justify-center">
                                                    <FileText className="w-5 h-5 text-white" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                                                        {file.name}
                                                    </p>
                                                    <p className="text-xs text-[var(--text-tertiary)]">
                                                        {formatFileSize(file.size)}
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeFile(index)}
                                                className="w-8 h-8 rounded-lg bg-[var(--neon-red)]/10 flex items-center justify-center text-[var(--neon-red)] opacity-0 group-hover:opacity-100 transition-opacity hover:bg-[var(--neon-red)]/20"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="flex justify-end gap-4 animate-slide-up stagger-2">
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="px-6 py-3 rounded-xl font-semibold text-[var(--text-secondary)] bg-[var(--bg-tertiary)] border border-[var(--border-primary)] hover:border-[var(--border-secondary)] transition-all duration-300"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={() => uploadMutation.mutate()}
                            disabled={files.length === 0 || uploadMutation.isPending}
                            className="btn-primary px-8 py-3 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {uploadMutation.isPending ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Zap className="w-5 h-5" />
                                    Start AI Analysis
                                </>
                            )}
                        </button>
                    </div>

                    <div className="card p-6 border-[var(--neon-cyan)]/20 animate-slide-up stagger-3">
                        <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-[var(--neon-cyan)]" />
                            AI Processing Pipeline
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {workflowSteps.map((step, index) => (
                                <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-primary)]">
                                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--neon-cyan)]/20 to-[var(--neon-purple)]/20 flex items-center justify-center text-[var(--neon-cyan)]">
                                        <step.icon className="w-4 h-4" />
                                    </div>
                                    <span className="text-sm text-[var(--text-secondary)]">{step.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}
