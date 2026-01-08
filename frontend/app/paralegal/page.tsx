'use client'

import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import ParalegalChat from '@/components/ParalegalChat'

export default function ParalegalPage() {
    return (
        <div className="p-6 h-screen flex flex-col overflow-hidden">
            <header className="mb-6 flex-shrink-0">
                <div className="flex items-center gap-3 mb-1">
                    <div className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-light)]">
                        <Sparkles className="w-5 h-5 text-[var(--gold-primary)]" />
                    </div>
                    <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Doc Chat</h1>
                </div>
                <p className="text-[var(--text-secondary)] text-sm">
                    Your dedicated AI assistant for rapid legal research, document summarization, and drafting support.
                </p>
            </header>

            <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="flex-1 min-h-0"
            >
                <ParalegalChat />
            </motion.div>
        </div>
    )
}
