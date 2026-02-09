'use client'

import { useQuery } from '@tanstack/react-query'
import { FolderOpen, Sparkles, Loader2, Library, AlertCircle } from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import MatterSummaryPanel from '@/components/MatterSummaryPanel'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'

export default function MattersPage() {
    const { data: matters = [], isLoading, error, refetch } = useQuery({
        queryKey: ['matters'],
        queryFn: () => api.getMatters(),
        refetchInterval: 10000, // Refetch every 10 seconds
        staleTime: 5000,
    })

    return (
        <div className="flex min-h-screen bg-[#0A0A0A] selection:bg-[#D4A853]/30">
            <Sidebar />

            <main className="flex-1 p-8 lg:p-12 relative overflow-hidden">
                {/* Archival Grain and Ambient Effects */}
                <div className="absolute inset-0 bg-[url('/grain.png')] opacity-[0.03] pointer-events-none"></div>
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#D4A853] opacity-[0.02] blur-[150px] rounded-full pointer-events-none"></div>

                <motion.div 
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-12 relative z-10"
                >
                    <div className="flex items-center gap-6 mb-8">
                        <div className="w-16 h-16 bg-[#1A1A1A] border border-[#D4A853]/40 flex items-center justify-center shadow-2xl">
                            <Library className="w-8 h-8 text-[#D4A853]" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3 text-[#D4A853] text-xs font-bold tracking-[0.3em] uppercase mb-1">
                                <span className="w-8 h-[1px] bg-[#D4A853]"></span>
                                Jurisprudential Repository
                                <span className="w-8 h-[1px] bg-[#D4A853]"></span>
                            </div>
                            <h1 className="text-5xl font-black text-white tracking-tighter uppercase font-serif italic">
                                Active <span className="text-[#D4A853] not-italic">Registry</span>
                            </h1>
                        </div>
                    </div>
                </motion.div>

                <AnimatePresence mode="wait">
                    {isLoading ? (
                        <motion.div 
                            key="loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="bg-[#141414] border border-[#D4A853]/10 p-24 text-center shadow-2xl"
                        >
                            <div className="relative inline-block mb-6">
                                <div className="absolute inset-0 bg-[#D4A853] blur-2xl opacity-10 animate-pulse"></div>
                                <Loader2 className="w-12 h-12 text-[#D4A853] animate-spin relative" />
                            </div>
                            <p className="text-[#D4A853] font-serif italic text-lg tracking-widest uppercase opacity-60">Synchronizing Archives...</p>
                        </motion.div>
                    ) : error ? (
                        <motion.div 
                            key="error"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="bg-[#141414] border border-red-500/20 p-24 text-center shadow-2xl"
                        >
                            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-6" />
                            <p className="text-red-500 font-serif text-lg tracking-widest uppercase opacity-60 mb-8">
                                Archive Synchronization Failed
                            </p>
                            <button 
                                onClick={() => refetch()}
                                className="px-8 py-4 bg-[#D4A853] text-white text-xs uppercase font-bold tracking-widest hover:bg-[#B88A3E] transition-all"
                            >
                                Retry Connection
                            </button>
                        </motion.div>
                    ) : (
                        <motion.div 
                            key="content"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="relative z-10"
                        >
                            <MatterSummaryPanel matters={matters} />
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>
        </div>
    )
}
