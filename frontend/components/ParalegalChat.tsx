'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, User, Bot, Paperclip, X, Sparkles, Loader2 } from 'lucide-react'

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    isStreaming?: boolean
}

export default function ParalegalChat() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: "Hello. I am your AI Paralegal. I can assist you with quick research, document summaries, or drafting tasks. How can I help you today?",
            timestamp: new Date()
        }
    ])
    const [input, setInput] = useState('')
    const [isStreaming, setIsStreaming] = useState(false)
    const [attachedFiles, setAttachedFiles] = useState<any[]>([])
    const [isUploading, setIsUploading] = useState(false)

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLTextAreaElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Auto-scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // Handle File Selection
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0]
            await uploadFile(file)
        }
    }

    // Upload to Backend
    const uploadFile = async (file: File) => {
        setIsUploading(true)
        const formData = new FormData()
        formData.append('file', file)

        try {
            const token = localStorage.getItem('access_token')
            const res = await fetch('/api/paralegal/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            })
            if (!res.ok) throw new Error('Upload failed')

            const data = await res.json()
            setAttachedFiles(prev => [...prev, { name: file.name, path: data.filepath }])
        } catch (error) {
            console.error(error)
        } finally {
            setIsUploading(false)
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    // Remove attachment
    const removeFile = (index: number) => {
        setAttachedFiles(prev => prev.filter((_, i) => i !== index))
    }

    // Handle Streaming Response
    const handleSend = async () => {
        if ((!input.trim() && attachedFiles.length === 0) || isStreaming) return

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim() + (attachedFiles.length > 0 ? `\n[Attached: ${attachedFiles.map(f => f.name).join(', ')}]` : ''),
            timestamp: new Date()
        }

        const contextFiles = attachedFiles.map(f => f.path)

        setMessages(prev => [...prev, userMsg])
        setInput('')
        setAttachedFiles([]) // Clear attachments after sending
        setIsStreaming(true)

        // Create placeholder for AI response
        const aiMsgId = (Date.now() + 1).toString()
        setMessages(prev => [...prev, {
            id: aiMsgId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true
        }])

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch('/api/paralegal/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: userMsg.content,
                    context_files: contextFiles
                })
            })

            if (!response.body) throw new Error("No response body")

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let aiContent = ""

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n\n')

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6))

                            if (data.type === 'token') {
                                aiContent += data.content
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId ? { ...m, content: aiContent } : m
                                ))
                            } else if (data.type === 'status') {
                                console.log("Status:", data.content)
                            } else if (data.type === 'error') {
                                aiContent += `\n[Error: ${data.content}]`
                            }
                        } catch (e) {
                            console.error("Error parsing SSE:", e)
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Chat error:", error)
            setMessages(prev => prev.map(m =>
                m.id === aiMsgId ? { ...m, content: "I apologize, but I encountered an error connecting to the server.", isStreaming: false } : m
            ))
        } finally {
            setIsStreaming(false)
            setMessages(prev => prev.map(m =>
                m.id === aiMsgId ? { ...m, isStreaming: false } : m
            ))
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="flex flex-col h-[calc(100vh-140px)] bg-[#0d1117] rounded-xl border border-[var(--border-light)] overflow-hidden shadow-2xl relative">
            {/* Ambient Background */}
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10 pointer-events-none"></div>
            <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--gold-primary)]/5 rounded-full blur-[100px] pointer-events-none"></div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 relative z-10 scrollbar-thin scrollbar-thumb-[var(--border-light)] scrollbar-track-transparent">
                {messages.map((msg) => (
                    <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                    >
                        {/* Avatar */}
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${msg.role === 'user'
                            ? 'bg-[var(--gold-primary)] text-black'
                            : 'bg-[var(--bg-tertiary)] border border-[var(--border-light)] text-[var(--gold-primary)]'
                            }`}>
                            {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>

                        {/* Content */}
                        <div className={`max-w-[75%] rounded-2xl p-4 ${msg.role === 'user'
                            ? 'bg-[#D4A853] text-black border border-[#D4A853] rounded-tr-sm shadow-lg font-medium'
                            : 'bg-white text-gray-800 border border-gray-200 rounded-tl-sm shadow-md'
                            }`}>
                            <div className={`prose prose-sm max-w-none leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'text-black' : 'text-gray-800'}`}>
                                {msg.content}
                                {msg.isStreaming && (
                                    <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-[var(--gold-primary)] animate-pulse" />
                                )}
                            </div>
                        </div>
                    </motion.div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-[var(--bg-card)] border-t border-[var(--border-light)] relative z-20">

                {/* File Attachments Preview */}
                <AnimatePresence>
                    {attachedFiles.length > 0 && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="flex gap-2 pb-3 overflow-x-auto"
                        >
                            {attachedFiles.map((file, i) => (
                                <div key={i} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border-light)] text-xs text-[var(--text-primary)]">
                                    <span className="truncate max-w-[150px]">{file.name}</span>
                                    <button onClick={() => removeFile(i)} className="text-[var(--text-tertiary)] hover:text-red-400">
                                        <X size={12} />
                                    </button>
                                </div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="relative flex items-end gap-2 bg-[var(--bg-tertiary)] p-2 rounded-xl border border-[var(--border-light)] focus-within:border-[var(--gold-primary)]/50 transition-colors shadow-inner">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        className="hidden"
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading || isStreaming}
                        className={`p-2 transition-colors rounded-lg hover:bg-[var(--bg-card)] ${isUploading ? 'text-[var(--gold-primary)] animate-pulse' : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'}`}
                    >
                        {isUploading ? <Loader2 size={20} className="animate-spin" /> : <Paperclip size={20} />}
                    </button>

                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask your paralegal anything..."
                        className="flex-1 bg-transparent border-none focus:ring-0 text-[var(--text-primary)] placeholder-[var(--text-tertiary)] resize-none max-h-32 min-h-[44px] py-2.5 text-sm"
                        rows={1}
                        disabled={isStreaming}
                    />

                    <button
                        onClick={() => handleSend()}
                        disabled={(!input.trim() && attachedFiles.length === 0) || isStreaming}
                        className={`p-2 rounded-lg transition-all duration-200 ${(input.trim() || attachedFiles.length > 0) && !isStreaming
                            ? 'bg-[var(--gold-primary)] text-black hover:scale-105 shadow-lg shadow-[var(--gold-primary)]/20'
                            : 'bg-[var(--bg-card)] text-[var(--text-tertiary)] cursor-not-allowed'
                            }`}
                    >
                        {isStreaming ? (
                            <Loader2 size={20} className="animate-spin" />
                        ) : (
                            <Send size={20} />
                        )}
                    </button>
                </div>
                <div className="px-2 pt-2 flex items-center justify-between text-[10px] text-[var(--text-tertiary)]">
                    <div className="flex items-center gap-1.5">
                        <Sparkles size={12} className="text-[var(--gold-primary)]" />
                        <span>AI Paralegal v1.0 • Connected</span>
                    </div>
                    <div>Press Enter to send, Shift + Enter for new line</div>
                </div>
            </div>
        </div>
    )
}
