'use client'

import { useState, useEffect } from 'react'
import { Shield, Scale, FileText, AlertTriangle, Gavel, Globe, Radio } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface SentinelEvent {
    id: number
    source: 'COURT' | 'INTERNAL' | 'LEXIS' | 'COMPLIANCE'
    title: string
    detail: string
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
    timestamp: string
}

const MOCK_EVENTS = [
    { source: 'COURT', title: 'Docket Update', detail: 'SDNY: Motion to Dismiss filed in State v. Blackwood', riskLevel: 'HIGH' },
    { source: 'LEXIS', title: 'Citation Alert', detail: 'New negative treatment: Harrison Estate Case', riskLevel: 'MEDIUM' },
    { source: 'COMPLIANCE', title: 'Risk Pattern', detail: 'Indemnity clause deviation detected in MTR-0891', riskLevel: 'HIGH' },
    { source: 'INTERNAL', title: 'Evidence Match', detail: 'Audio transcript matches deposition #44', riskLevel: 'LOW' },
    { source: 'COURT', title: 'Hearing Scheduled', detail: 'Delaware Chancery: Scheduling Conference', riskLevel: 'MEDIUM' },
    { source: 'LEXIS', title: 'Statute Update', detail: 'Amendment to IP Regulation 4.2 effective immediately', riskLevel: 'LOW' },
]

export default function LegalSentinel() {
    const [events, setEvents] = useState<SentinelEvent[]>([])
    const [scanning, setScanning] = useState(true)

    useEffect(() => {
        // Initial load
        setEvents(MOCK_EVENTS.slice(0, 3).map((e, i) => ({ ...e, id: i, source: e.source as any, riskLevel: e.riskLevel as any, timestamp: 'Now' })))

        const interval = setInterval(() => {
            const randomEvent = MOCK_EVENTS[Math.floor(Math.random() * MOCK_EVENTS.length)]
            const newEvent = {
                ...randomEvent,
                id: Date.now(),
                source: randomEvent.source as any,
                riskLevel: randomEvent.riskLevel as any,
                timestamp: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit' })
            }

            setEvents(prev => [newEvent, ...prev].slice(0, 5))
        }, 3000)

        return () => clearInterval(interval)
    }, [])

    return (
        <div className="bg-[#121212] border border-[#333] rounded-lg shadow-lg flex flex-col h-[450px] overflow-hidden relative group hover:border-[#C9A24D]/30 transition-all duration-500">

            {/* Header with Radar Icon */}
            <div className="px-6 py-4 border-b border-[#333] bg-[#141414] flex justify-between items-center z-10">
                <div className="flex items-center gap-3">
                    <div className="relative flex items-center justify-center w-6 h-6">
                        <Radio className="w-5 h-5 text-[#C9A24D] relative z-10" />
                        <span className="absolute w-full h-full bg-[#C9A24D]/20 rounded-full animate-ping" />
                    </div>
                    <div>
                        <h2 className="text-sm font-serif font-bold text-[#EAEAEA] tracking-wide">Legal Sentinel</h2>
                        <span className="text-[9px] text-[#525252] font-mono uppercase tracking-[0.2em] block mt-0.5">Active Monitoring</span>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-2 py-1 bg-[#262626] rounded border border-[#333]">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[9px] font-bold text-[#9A9A9A]">SECURE</span>
                </div>
            </div>

            {/* Visualizer Area - The "Unique" Part */}
            <div className="relative h-32 bg-[#0B0B0B] border-b border-[#333] overflow-hidden flex items-center justify-center">
                {/* Radar Grid */}
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#1A1A1A] to-[#0B0B0B]" />
                <div className="absolute inset-0 opacity-20"
                    style={{ backgroundImage: 'radial-gradient(circle, #333 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
                </div>

                {/* Scanning Line */}
                <div className="absolute w-full h-[1px] bg-gradient-to-r from-transparent via-[#C9A24D]/50 to-transparent top-1/2 -translate-y-1/2 animate-scan-vertical" />

                {/* Central Pulse */}
                <div className="relative z-10 flex flex-col items-center">
                    <div className="w-16 h-16 rounded-full border border-[#C9A24D]/30 flex items-center justify-center relative">
                        <div className="absolute inset-0 rounded-full border border-[#C9A24D]/10 animate-ping" />
                        <Shield className="w-6 h-6 text-[#C9A24D]" />
                    </div>
                    <span className="text-[9px] text-[#C9A24D] font-mono mt-2 tracking-widest">SCANNING DOCKETS</span>
                </div>
            </div>

            {/* Event Stream */}
            <div className="flex-1 p-0 overflow-y-auto custom-scrollbar bg-[#0F0F0F]">
                <AnimatePresence initial={false}>
                    {events.map((event) => (
                        <motion.div
                            key={event.id}
                            initial={{ opacity: 0, x: -10, backgroundColor: "rgba(201, 162, 77, 0.1)" }}
                            animate={{ opacity: 1, x: 0, backgroundColor: "rgba(0,0,0,0)" }}
                            transition={{ duration: 0.5 }}
                            className="p-4 border-b border-[#1A1A1A] hover:bg-[#1A1A1A] transition-colors group/item"
                        >
                            <div className="flex justify-between items-start mb-1">
                                <div className="flex items-center gap-2">
                                    {event.source === 'COURT' && <Gavel className="w-3 h-3 text-[#EAEAEA]" />}
                                    {event.source === 'LEXIS' && <Globe className="w-3 h-3 text-blue-400" />}
                                    {event.source === 'COMPLIANCE' && <Shield className="w-3 h-3 text-[#C9A24D]" />}
                                    {event.source === 'INTERNAL' && <FileText className="w-3 h-3 text-[#525252]" />}
                                    <span className="text-[9px] font-bold text-[#737373] tracking-wider">{event.source}</span>
                                </div>
                                <span className="text-[9px] font-mono text-[#525252]">{event.timestamp}</span>
                            </div>

                            <h4 className="text-xs font-bold text-[#EAEAEA] mb-1 group-hover/item:text-[#C9A24D] transition-colors">
                                {event.title}
                            </h4>
                            <p className="text-[10px] text-[#9A9A9A] leading-relaxed">
                                {event.detail}
                            </p>

                            {event.riskLevel === 'HIGH' && (
                                <div className="mt-2 flex items-center gap-1 text-[#8B2E2E]">
                                    <AlertTriangle className="w-3 h-3" />
                                    <span className="text-[9px] font-bold">RISK DETECTED</span>
                                </div>
                            )}
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    )
}
