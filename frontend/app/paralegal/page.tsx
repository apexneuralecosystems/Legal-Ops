'use client'

import { motion } from 'framer-motion'
import { ExternalLink, Sparkles, Zap, Shield, Bot } from 'lucide-react'
import Link from 'next/link'

export default function ParalegalPage() {
    return (
        <div className="p-8">
            <header className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-light)]">
                        <Bot className="w-6 h-6 text-[var(--gold-primary)]" />
                    </div>
                    <h1 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight">AI Paralegal</h1>
                </div>
                <p className="text-[var(--text-secondary)] max-w-2xl">
                    Access our specialized experimental paralegal interface for quick tasks and document analysis.
                </p>
            </header>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-4xl"
            >
                <div className="glass-card p-8 rounded-2xl relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-[var(--bg-tertiary)] to-transparent opacity-50"></div>
                    <div className="absolute -right-20 -top-20 w-64 h-64 bg-[var(--gold-primary)]/10 rounded-full blur-3xl group-hover:bg-[var(--gold-primary)]/20 transition-all duration-700"></div>

                    <div className="relative z-10">
                        <div className="flex flex-col md:flex-row gap-8 items-start">
                            <div className="flex-1 space-y-6">
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--gold-primary)]/10 border border-[var(--gold-primary)]/20 text-[var(--gold-primary)] text-xs font-bold tracking-wider">
                                    <Sparkles className="w-3 h-3" />
                                    <span>MINI PROJECT</span>
                                </div>

                                <h2 className="text-3xl font-bold text-[var(--text-primary)]">
                                    ApexNeural Paralegal Suite
                                </h2>

                                <p className="text-[var(--text-secondary)] text-lg leading-relaxed">
                                    This specialized micro-application serves as a lightweight, focused interface for rapid legal document processing and quick queries. It operates as a complementary module to the main LegalOps system.
                                </p>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {[
                                        { icon: Zap, label: "Rapid Processing", desc: "Optimized for speed" },
                                        { icon: Shield, label: "Secure Sandbox", desc: "Isolated environment" },
                                    ].map((feature, i) => (
                                        <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-[var(--bg-tertiary)]/50 border border-[var(--border-light)]">
                                            <feature.icon className="w-5 h-5 text-[var(--gold-primary)] mt-0.5" />
                                            <div>
                                                <p className="font-semibold text-[var(--text-primary)] text-sm">{feature.label}</p>
                                                <p className="text-xs text-[var(--text-tertiary)]">{feature.desc}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="pt-4">
                                    <a
                                        href="https://paralegal.apexneural.cloud/"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-[var(--gold-primary)] to-[var(--gold-dark)] text-[#0d1117] font-bold text-lg shadow-lg shadow-[var(--gold-primary)]/20 hover:shadow-[var(--gold-primary)]/40 hover:scale-[1.02] transition-all duration-300"
                                    >
                                        <span>Launch Paralegal Application</span>
                                        <ExternalLink className="w-5 h-5" />
                                    </a>
                                    <p className="mt-3 text-xs text-[var(--text-tertiary)] flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--gold-primary)] animate-pulse"></span>
                                        Opens in a new distinct environment
                                    </p>
                                </div>
                            </div>

                            <div className="w-full md:w-1/3 aspect-video md:aspect-square rounded-xl bg-[#0d1117] border border-[var(--border-light)] flex items-center justify-center relative overflow-hidden shadow-2xl">
                                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20"></div>
                                {/* Abstract UI Representation */}
                                <div className="w-3/4 h-3/4 bg-[var(--bg-card)] rounded-lg border border-[var(--border-light)] p-4 space-y-3 relative z-10 transform rotate-3 hover:rotate-0 transition-transform duration-500 shadow-xl">
                                    <div className="flex items-center gap-2 pb-2 border-b border-[var(--border-light)]">
                                        <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                                        <div className="w-2 h-2 rounded-full bg-yellow-500/50"></div>
                                        <div className="w-2 h-2 rounded-full bg-green-500/50"></div>
                                    </div>
                                    <div className="h-2 w-1/3 bg-[var(--text-tertiary)]/20 rounded-full"></div>
                                    <div className="space-y-2 pt-2">
                                        <div className="h-2 w-full bg-[var(--text-tertiary)]/10 rounded-full"></div>
                                        <div className="h-2 w-5/6 bg-[var(--text-tertiary)]/10 rounded-full"></div>
                                        <div className="h-2 w-4/6 bg-[var(--text-tertiary)]/10 rounded-full"></div>
                                    </div>
                                    <div className="absolute bottom-4 right-4 w-8 h-8 rounded-full bg-[var(--gold-primary)] flex items-center justify-center shadow-lg shadow-[var(--gold-primary)]/30">
                                        <Bot className="w-4 h-4 text-[#0d1117]" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    )
}
