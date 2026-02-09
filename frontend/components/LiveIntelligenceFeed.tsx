'use client'

import { useState, useEffect, useRef } from 'react'
import { Activity, Wifi, Shield, Database, Search, Terminal, Zap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface LogEntry {
    id: number
    timestamp: string
    agent: string
    message: string
    type: 'INFO' | 'SUCCESS' | 'WARNING' | 'CRITICAL'
}

const AGENTS = ['LEX-CORE', 'EVIDENCE', 'DRAFTING', 'SECURITY', 'NETWORK']
const MESSAGES = [
    'Cross-referencing active session tokens...',
    'Encrypting data packet #8821...',
    'Indexing new deposition transcripts...',
    'Optimizing query latency...',
    'Detected minor variance in case law...',
    'Syncing local cache with master registry...',
    'Verifying biometric signatures...',
    'Allocating GPU resources for synthesis...',
    'Running background risk heuristic...',
    'Connection to LexisNexis stable.'
]

export default function LiveIntelligenceFeed() {
    const [logs, setLogs] = useState<LogEntry[]>([])

    // Initialize with some data
    useEffect(() => {
        const initialLogs = Array.from({ length: 6 }).map((_, i) => generateLog(i))
        setLogs(initialLogs)

        const interval = setInterval(() => {
            setLogs(prev => {
                const newLog = generateLog(Date.now())
                const newLogs = [...prev, newLog]
                if (newLogs.length > 8) newLogs.shift() // Keep only last 8 items
                return newLogs
            })
        }, 1500 + Math.random() * 2000) // Random interval between 1.5s and 3.5s

        return () => clearInterval(interval)
    }, [])

    const generateLog = (id: number): LogEntry => {
        const typeRoll = Math.random()
        let type: LogEntry['type'] = 'INFO'
        if (typeRoll > 0.8) type = 'SUCCESS'
        if (typeRoll > 0.95) type = 'WARNING'

        return {
            id,
            timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            agent: AGENTS[Math.floor(Math.random() * AGENTS.length)],
            message: MESSAGES[Math.floor(Math.random() * MESSAGES.length)],
            type
        }
    }

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'SUCCESS': return 'text-emerald-500'
            case 'WARNING': return 'text-[#C9A24D]'
            case 'CRITICAL': return 'text-[#8B2E2E]'
            default: return 'text-[#9A9A9A]'
        }
    }

    return (
        <div className="bg-[#121212] border border-[#333] rounded-lg shadow-[0_4px_20px_rgba(0,0,0,0.5)] flex flex-col h-[400px] overflow-hidden relative group hover:border-[#C9A24D]/30 transition-colors">

            {/* Header */}
            <div className="px-6 py-4 border-b border-[#333] bg-[#141414] flex justify-between items-center z-10">
                <div className="flex items-center gap-3">
                    <Activity className="w-4 h-4 text-[#C9A24D] animate-pulse" />
                    <div>
                        <h2 className="text-sm font-serif font-bold text-[#EAEAEA] tracking-wide">Live Intelligence</h2>
                        <span className="text-[9px] text-[#525252] font-mono uppercase tracking-[0.2em] relative top-[1px]">Real-time Feed</span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1.5 px-2 py-1 bg-[#0B0B0B] rounded border border-[#333]">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[9px] font-mono text-[#737373]">LIVE</span>
                    </div>
                    <Wifi className="w-3 h-3 text-[#525252]" />
                </div>
            </div>

            {/* Scanline Overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#C9A24D]/[0.02] to-transparent pointer-events-none animate-scanline z-0" />

            {/* Content Actions */}
            <div className="flex-1 p-6 relative overflow-hidden font-mono text-xs">

                <div className="absolute bottom-6 left-6 right-6 flex flex-col justify-end gap-3">
                    <AnimatePresence initial={false}>
                        {logs.map((log) => (
                            <motion.div
                                key={log.id}
                                initial={{ opacity: 0, x: -20, height: 0 }}
                                animate={{ opacity: 1, x: 0, height: 'auto' }}
                                exit={{ opacity: 0, x: 20, height: 0 }}
                                transition={{ duration: 0.3 }}
                                className="flex items-start gap-3 border-l-2 border-[#333] pl-3 py-1"
                            >
                                <span className="text-[#525252] whitespace-nowrap text-[10px]">{log.timestamp}</span>
                                <div className="flex flex-col">
                                    <div className="flex items-center gap-2">
                                        <span className="text-[#C9A24D] font-bold text-[10px] tracking-wider">[{log.agent}]</span>
                                    </div>
                                    <span className={`${getTypeColor(log.type)} leading-tight`}>{log.message}</span>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>

                {/* Fade to Black at Top */}
                <div className="absolute top-0 left-0 right-0 h-20 bg-gradient-to-b from-[#121212] to-transparent pointer-events-none" />

            </div>

            {/* Footer Status */}
            <div className="px-4 py-2 border-t border-[#333] bg-[#0B0B0B] flex justify-between items-center text-[9px] text-[#525252] font-mono uppercase">
                <span>Latency: 12ms</span>
                <span>Encrypted: AES-256</span>
            </div>
        </div>
    )
}
