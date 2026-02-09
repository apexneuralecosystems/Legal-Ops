'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, User, Bot, Paperclip, X, Sparkles, Loader2, Scale, Search, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    isStreaming?: boolean
    status?: string
}

interface AttachedFile {
    name: string
    path: string
}

interface ParalegalChatProps {
    matterId?: string
}

interface StreamData {
    type: 'token' | 'status' | 'error'
    content: string
}

const MAX_STORED_MESSAGES = 50
const SUGGESTED_QUESTION_MIN_LENGTH = 5
const API_BASE_URL = '/api/paralegal'

export default function ParalegalChat({ matterId }: ParalegalChatProps) {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [isStreaming, setIsStreaming] = useState(false)
    const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([])
    const [isUploading, setIsUploading] = useState(false)
    const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([
        "What are the key facts of this case?",
        "Summarize the main legal issues",
        "What evidence supports the plaintiff's position?",
        "Identify potential weaknesses in the defense"
    ])
    const [loadingQuestions, setLoadingQuestions] = useState(false)
    const [mode, setMode] = useState<'analysis' | 'argument'>('analysis')
    const [enableDevil, setEnableDevil] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLTextAreaElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [])

    useEffect(() => {
        scrollToBottom()
    }, [messages, scrollToBottom])

    const getWelcomeMessage = useCallback((): Message => ({
        id: 'welcome',
        role: 'assistant',
        content: matterId
            ? "Hello. I am your Case Assistant. I have read the files for this matter. You can ask me anything about them."
            : "Hello. I am your AI Doc Chat Assistant. I can assist you with quick research or document summaries. How can I help you today?",
        timestamp: new Date()
    }), [matterId])

    useEffect(() => {
        if (typeof window === 'undefined') return

        const key = `paralegal_chat_${matterId || 'general'}`
        const raw = localStorage.getItem(key)

        if (raw) {
            try {
                const parsed = JSON.parse(raw) as { id: string; role: 'user' | 'assistant'; content: string; timestamp: string; isStreaming?: boolean }[]
                const restored: Message[] = parsed.map(m => ({
                    id: m.id,
                    role: m.role,
                    content: m.content,
                    timestamp: new Date(m.timestamp),
                    isStreaming: false // Reset streaming state on restore
                }))
                setMessages(restored)
                return
            } catch (e) {
                console.error('Failed to restore Doc Chat history:', e)
                localStorage.removeItem(key) // Clean up corrupted data
            }
        }

        setMessages([getWelcomeMessage()])
    }, [matterId, getWelcomeMessage])

    useEffect(() => {
        if (typeof window === 'undefined' || messages.length === 0) return

        const key = `paralegal_chat_${matterId || 'general'}`
        const toStore = messages.slice(-MAX_STORED_MESSAGES).map(m => ({
            id: m.id,
            role: m.role,
            content: m.content,
            timestamp: m.timestamp.toISOString(),
            isStreaming: false // Don't persist streaming state
        }))

        try {
            localStorage.setItem(key, JSON.stringify(toStore))
        } catch (e) {
            console.error('Failed to save chat history:', e)
        }
    }, [messages, matterId])

    const fetchSuggestedQuestions = useCallback(async () => {
        // Default fallback suggestions
        const defaultSuggestions = matterId ? [
            "What are the key facts of this case?",
            "Summarize the main legal issues",
            "What evidence supports the plaintiff's position?",
            "Identify potential weaknesses in the defense",
            "What are the relevant precedents?"
        ] : [
            "How can I help you today?",
            "Summarize a legal document",
            "Research case law on a topic"
        ]

        if (!matterId) {
            setSuggestedQuestions(defaultSuggestions)
            return
        }

        setLoadingQuestions(true)
        setError(null)

        try {
            const token = localStorage.getItem('access_token')
            if (!token) {
                console.warn('No access token available')
                setSuggestedQuestions(defaultSuggestions)
                return
            }

            const res = await fetch(`${API_BASE_URL}/suggested-questions/${matterId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })

            if (!res.ok) {
                throw new Error(`Failed to fetch suggestions: ${res.status}`)
            }

            const data = await res.json()
            const questions = Array.isArray(data.suggested_questions) ? data.suggested_questions : []
            setSuggestedQuestions(questions.length > 0 ? questions : defaultSuggestions)
        } catch (error) {
            console.error('Failed to fetch suggested questions:', error)
            // Use fallback suggestions on error
            setSuggestedQuestions(defaultSuggestions)
        } finally {
            setLoadingQuestions(false)
        }
    }, [matterId])

    useEffect(() => {
        fetchSuggestedQuestions()
    }, [fetchSuggestedQuestions])

    const handleSuggestedClick = useCallback((question: string) => {
        setInput(question)
        setTimeout(() => inputRef.current?.focus(), 0)
    }, [])

    const handleCopyLatestAnswer = useCallback(async () => {
        const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant')
        if (!lastAssistant || !lastAssistant.content.trim()) return

        if (typeof navigator === 'undefined' || !navigator.clipboard) {
            console.warn('Clipboard API not available')
            return
        }

        try {
            await navigator.clipboard.writeText(lastAssistant.content)
            setError(null)
        } catch (e) {
            console.error('Failed to copy answer:', e)
            setError('Failed to copy to clipboard')
        }
    }, [messages])

    const handleClearChat = useCallback(() => {
        if (isStreaming) return

        const key = `paralegal_chat_${matterId || 'general'}`
        if (typeof window !== 'undefined') {
            try {
                localStorage.removeItem(key)
            } catch (e) {
                console.error('Failed to clear chat history:', e)
            }
        }

        setMessages([getWelcomeMessage()])
        setError(null)
    }, [isStreaming, matterId, getWelcomeMessage])

    // Handle File Selection
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0]
            await uploadFile(file)
        }
    }

    // Upload to Backend
    const uploadFile = useCallback(async (file: File) => {
        setIsUploading(true)
        setError(null)

        const formData = new FormData()
        formData.append('file', file)
        formData.append('matter_id', matterId || 'general')

        try {
            const token = localStorage.getItem('access_token')
            if (!token) {
                throw new Error('Authentication required')
            }

            const res = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            })

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                throw new Error(errorData.message || `Upload failed: ${res.status}`)
            }

            const data = await res.json()
            if (!data.filepath) {
                throw new Error('Invalid server response: missing filepath')
            }

            setAttachedFiles(prev => [...prev, { name: file.name, path: data.filepath }])
        } catch (error) {
            console.error('Upload error:', error)
            setError(error instanceof Error ? error.message : 'Failed to upload file')
        } finally {
            setIsUploading(false)
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }, [matterId])

    // Remove attachment
    const removeFile = useCallback((index: number) => {
        setAttachedFiles(prev => prev.filter((_, i) => i !== index))
    }, [])

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
            isStreaming: true,
            status: "Connecting..."
        }])

        try {
            const token = localStorage.getItem('access_token')
            if (!token) {
                throw new Error('Authentication required. Please log in again.')
            }

            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: userMsg.content,
                    context_files: contextFiles,
                    matter_id: matterId,
                    mode,
                    enable_devil: enableDevil
                })
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.message || `Request failed: ${response.status}`)
            }

            if (!response.body) throw new Error("No response body received")

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let aiContent = ""
            let buffer = "" // Buffer for incomplete SSE data

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                // Append to buffer with streaming decode
                buffer += decoder.decode(value, { stream: true })

                // Process complete messages
                const messages = buffer.split('\n\n')
                buffer = messages.pop() || '' // Keep incomplete data in buffer

                for (const message of messages) {
                    if (message.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(message.slice(6)) as StreamData

                            if (data.type === 'token' && data.content) {
                                aiContent += data.content
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId ? { ...m, content: aiContent, status: undefined } : m
                                ))
                            } else if (data.type === 'status' && data.content) {
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId ? { ...m, status: data.content } : m
                                ))
                            } else if (data.type === 'error') {
                                const errorMsg = data.content || 'Unknown error occurred'
                                aiContent += `\n\n⚠️ **Error**: ${errorMsg}`
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId ? { ...m, content: aiContent, status: undefined } : m
                                ))
                                setError(errorMsg)
                            }
                        } catch (e) {
                            console.error("Error parsing SSE:", e, message)
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Chat error:", error)
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            setError(errorMessage)
            setMessages(prev => prev.map(m =>
                m.id === aiMsgId ? {
                    ...m,
                    content: "I apologize, but I encountered an error connecting to the server. Please try again.",
                    isStreaming: false
                } : m
            ))
        } finally {
            setIsStreaming(false)
            setMessages(prev => prev.map(m =>
                m.id === aiMsgId ? { ...m, isStreaming: false } : m
            ))
        }
    }

    const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey && !isStreaming) {
            e.preventDefault()
            void handleSend()
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isStreaming])

    return (
        <div className="flex flex-col h-[calc(100vh-140px)] bg-[#0a0a0a] rounded-xl shadow-2xl relative">
            {/* Clean background like ChatGPT */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0a] to-[#111] pointer-events-none rounded-xl"></div>

            {/* Error Banner */}
            {error && (
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 max-w-md"
                >
                    <span className="text-sm">{error}</span>
                    <button onClick={() => setError(null)} className="ml-2 hover:text-red-300">
                        <X size={14} />
                    </button>
                </motion.div>
            )}

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 relative z-10">
                {messages.map((msg) => (
                    <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                    >
                        {/* Avatar */}
                        <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user'
                            ? 'bg-gradient-to-br from-[#D4A853] to-[#B88A3E] text-white'
                            : 'bg-[#1a1a1a] border border-[#333] text-[#D4A853]'
                            }`}>
                            {msg.role === 'user' ? <User size={16} /> : <Scale size={16} />}
                        </div>

                        {/* Message Content - ChatGPT style */}
                        <div className={`flex-1 max-w-3xl ${msg.role === 'user' ? 'text-right' : ''}`}>
                            <div className={`inline-block text-left rounded-2xl px-4 py-3 ${msg.role === 'user'
                                ? 'bg-[#2a2a2a] text-white'
                                : 'bg-transparent text-[#e5e5e5]'
                                }`}>
                                <div className={`prose prose-sm max-w-none leading-relaxed ${msg.role === 'user' ? 'text-white whitespace-pre-wrap' : 'text-[#e5e5e5] prose-headings:text-white prose-strong:text-white prose-table:text-sm'}`}>
                                    {msg.role === 'assistant' ? (
                                        <div className="space-y-4">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    hr: () => <hr className="my-4 border-[#333]" />,
                                                    h1: (props) => <h1 className="text-xl font-bold mb-4 text-white mt-6 pb-2 border-b border-[#333]" {...props} />,
                                                    h2: (props) => <h2 className="text-lg font-semibold mb-3 text-[#D4A853] mt-5" {...props} />,
                                                    h3: (props) => <h3 className="text-base font-semibold mb-2 text-white mt-4" {...props} />,
                                                    ul: (props) => <ul className="list-disc pl-5 my-3 space-y-1 text-[#d4d4d4]" {...props} />,
                                                    ol: (props) => <ol className="list-decimal pl-5 my-3 space-y-1 text-[#d4d4d4]" {...props} />,
                                                    li: (props) => <li className="mb-1" {...props} />,
                                                    p: (props) => <p className="mb-3 leading-relaxed text-[#e5e5e5]" {...props} />,
                                                    strong: (props) => <strong className="font-bold text-white" {...props} />,
                                                    code: (props) => <code className="bg-[#111] px-1.5 py-0.5 rounded text-xs font-mono text-[#D4A853] border border-[#333]" {...props} />,
                                                    blockquote: (props) => <blockquote className="border-l-2 border-[#D4A853] pl-4 my-3 italic text-[#999]" {...props} />,
                                                    a: (props) => (
                                                        <a
                                                            className="text-[#D4A853] hover:text-[#E8C775] hover:underline underline-offset-4 decoration-[#D4A853]/40 transition-all font-medium inline-flex items-center gap-1"
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            {...props}
                                                        >
                                                            {props.children}
                                                            <ExternalLink size={10} strokeWidth={2.5} />
                                                        </a>
                                                    ),
                                                }}
                                            >
                                                {msg.content}
                                            </ReactMarkdown>

                                            {msg.isStreaming && msg.status && (
                                                <div className="flex items-center gap-2 mt-3 text-xs text-[#D4A853] opacity-80">
                                                    <Loader2 size={12} className="animate-spin" />
                                                    {msg.status}
                                                </div>
                                            )}

                                            {!msg.isStreaming && msg.content.includes("### Suggested Next Steps") && (
                                                <div className="mt-4 pt-3 border-t border-[#333]">
                                                    <p className="text-[10px] uppercase tracking-wider text-[#888] mb-3 font-medium flex items-center gap-2">
                                                        <Sparkles size={10} className="text-[#D4A853]" /> Follow-up Questions
                                                    </p>
                                                    <div className="flex flex-col gap-2">
                                                        {(() => {
                                                            const parts = msg.content.split("### Suggested Next Steps")
                                                            if (parts.length < 2) return null

                                                            const questionsSection = parts[1].split("### 📚 Sources Used")[0] || parts[1]

                                                            return questionsSection
                                                                .split("\n")
                                                                .filter(line => {
                                                                    const trim = line.trim()
                                                                    return trim.startsWith("-") || trim.startsWith("1.") || /^\d+\./.test(trim)
                                                                })
                                                                .map((q, idx) => {
                                                                    const cleanQ = q.replace(/^[-\d.*•]\s*/, "").trim()
                                                                    if (!cleanQ || cleanQ.length < SUGGESTED_QUESTION_MIN_LENGTH) return null
                                                                    return (
                                                                        <button
                                                                            key={idx}
                                                                            onClick={() => {
                                                                                setInput(cleanQ);
                                                                                setTimeout(() => {
                                                                                    const btn = document.querySelector('button[aria-label="Send message"]') as HTMLButtonElement;
                                                                                    if (btn) btn.click();
                                                                                    else void handleSend();
                                                                                }, 100);
                                                                            }}
                                                                            className="text-left text-sm bg-[#1a1a1a] hover:bg-[#252525] border border-[#333] hover:border-[#D4A853] p-3 rounded-lg transition-all text-[#aaa] hover:text-[#D4A853] flex items-start gap-3"
                                                                        >
                                                                            <Send size={14} className="mt-0.5 text-[#666] group-hover:text-[#D4A853]" />
                                                                            <span>{cleanQ}</span>
                                                                        </button>
                                                                    )
                                                                })
                                                        })()}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        msg.content
                                    )}
                                    {msg.isStreaming && (
                                        <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-[#D4A853] animate-pulse rounded-sm" />
                                    )}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                ))}
                {/* Suggested Questions - proper placement inside scrollview */}
                {suggestedQuestions.length > 0 && messages.length <= 4 && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="py-4 mt-2 px-2"
                    >
                        <p className="text-xs uppercase tracking-wider text-[#D4A853] mb-3 font-bold flex items-center gap-2 opacity-80">
                            <Sparkles size={12} className="text-[#D4A853]" /> Suggested Follow-ups
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {suggestedQuestions.map((q, i) => (
                                <button
                                    key={i}
                                    onClick={() => handleSuggestedClick(q)}
                                    className="text-left px-4 py-3 text-sm bg-[#1a1a1a] border border-[#333] hover:border-[#D4A853]/50 hover:bg-[#D4A853]/5 rounded-lg transition-all text-[#e5e5e5] hover:text-white shadow-sm group"
                                >
                                    <span className="line-clamp-2">{q}</span>
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}

                <div ref={messagesEndRef} />
            </div>



            {loadingQuestions && (
                <div className="flex-shrink-0 px-4 py-2 text-xs text-[#D4A853] flex items-center gap-2 bg-[#111] border-t border-[#333]">
                    <Loader2 size={12} className="animate-spin" />
                    Loading suggestions...
                </div>
            )}

            {/* Input Area */}
            <div className="flex-shrink-0 p-3 bg-[#0a0a0a] border-t border-[#333] relative z-20">

                {/* File Attachments Preview */}
                <AnimatePresence>
                    {attachedFiles.length > 0 && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="flex gap-2 pb-2 overflow-x-auto"
                        >
                            {attachedFiles.map((file, i) => (
                                <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1a1a1a] border border-[#333] text-xs text-white">
                                    <Paperclip size={12} className="text-[#D4A853]" />
                                    <span className="truncate max-w-[150px]">{file.name}</span>
                                    <button onClick={() => removeFile(i)} className="text-[#888] hover:text-red-400">
                                        <X size={14} />
                                    </button>
                                </div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="relative flex items-end gap-2 bg-[#1a1a1a] p-2 rounded-2xl border border-[#333] focus-within:border-[#D4A853]/50 transition-all">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        className="hidden"
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading || isStreaming}
                        className={`p-2 transition-colors rounded-lg hover:bg-[#252525] ${isUploading ? 'text-[#D4A853] animate-pulse' : 'text-[#888] hover:text-white'}`}
                        aria-label="Attach file"
                        title="Attach file"
                    >
                        {isUploading ? <Loader2 size={20} className="animate-spin" /> : <Paperclip size={20} />}
                    </button>

                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Message Legal Assistant..."
                        className="flex-1 bg-transparent border-none focus:ring-0 focus:outline-none text-white placeholder-[#666] resize-none max-h-32 min-h-[40px] py-2 px-2 text-sm"
                        rows={1}
                        disabled={isStreaming}
                        aria-label="Chat message input"
                    />

                    <button
                        onClick={() => void handleSend()}
                        disabled={(!input.trim() && attachedFiles.length === 0) || isStreaming}
                        className={`p-2 rounded-lg transition-all ${(input.trim() || attachedFiles.length > 0) && !isStreaming
                            ? 'bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-white hover:from-[#E8C775] hover:to-[#D4A853]'
                            : 'bg-[#252525] text-[#555] cursor-not-allowed'
                            }`}
                        aria-label="Send message"
                        title="Send message"
                    >
                        {isStreaming ? (
                            <Loader2 size={18} className="animate-spin" />
                        ) : (
                            <Send size={18} />
                        )}
                    </button>
                </div>

                <div className="px-1 pt-2 flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                        {/* Mode Selectors */}
                        <div className="flex items-center gap-1 border border-[#333] rounded-lg p-1 bg-[#111]">
                            <button
                                type="button"
                                onClick={() => !isStreaming && setMode('analysis')}
                                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${mode === 'analysis' ? 'bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-white' : 'text-[#888] hover:text-white'}`}
                            >
                                Analysis
                            </button>
                            <button
                                type="button"
                                onClick={() => !isStreaming && setMode('argument')}
                                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${mode === 'argument' ? 'bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-white' : 'text-[#888] hover:text-white'}`}
                            >
                                Challenge
                            </button>
                        </div>

                        <div className="h-4 w-[1px] bg-[#333] hidden md:block" />

                        <button
                            type="button"
                            onClick={() => !isStreaming && setEnableDevil(!enableDevil)}
                            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${enableDevil
                                ? 'bg-red-500/10 border-red-500/50 text-red-400'
                                : 'border-[#333] text-[#888] hover:text-white hover:border-[#555]'}`}
                        >
                            {enableDevil ? '🔥 Devil Mode' : 'Devil Mode'}
                        </button>

                        <div className="h-4 w-[1px] bg-[#333] hidden md:block" />

                        {/* Research Cases Button */}
                        <button
                            type="button"
                            onClick={() => {
                                // Extract topics from recent user messages
                                const userMessages = messages.filter(m => m.role === 'user').slice(-3);
                                const topics = userMessages.map(m => m.content).join(' ');
                                const query = topics.substring(0, 200) || 'legal research';
                                const url = `/research?query=${encodeURIComponent(query)}${matterId ? `&matter=${matterId}` : ''}`;
                                window.open(url, '_blank');
                            }}
                            className="px-3 py-1.5 rounded-lg border border-[#D4A853] text-xs text-[#D4A853] hover:bg-[#D4A853]/10 transition-all flex items-center gap-1"
                        >
                            <Search size={12} /> Research Cases
                        </button>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={handleCopyLatestAnswer}
                            disabled={!messages.some(m => m.role === 'assistant')}
                            className="px-3 py-1.5 rounded-lg border border-[#333] text-xs text-[#888] hover:text-[#D4A853] hover:border-[#D4A853] transition-all disabled:opacity-30"
                        >
                            Copy
                        </button>
                        <button
                            type="button"
                            onClick={handleClearChat}
                            disabled={isStreaming}
                            className="px-3 py-1.5 rounded-lg border border-[#333] text-xs text-[#888] hover:text-red-400 hover:border-red-400 transition-all disabled:opacity-30"
                        >
                            Clear
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

