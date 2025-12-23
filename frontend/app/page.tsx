import Link from 'next/link'
import { FileText, Scale, Search, ArrowRight, Shield, Sparkles, Zap, Brain, Globe, ChevronRight } from 'lucide-react'

export default function Home() {
    return (
        <main className="min-h-screen flex flex-col bg-[var(--bg-primary)] relative overflow-hidden">
            <div className="absolute inset-0 bg-grid opacity-50"></div>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-[var(--gold-primary)] opacity-[0.06] blur-[150px] rounded-full"></div>
            <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-[var(--teal-primary)] opacity-[0.06] blur-[150px] rounded-full"></div>
            <div className="absolute top-1/2 left-0 w-[400px] h-[400px] bg-[var(--gold-dark)] opacity-[0.04] blur-[120px] rounded-full"></div>

            <nav className="relative z-10 flex items-center justify-between px-8 py-6 border-b border-[var(--border-light)]">
                <Link href="/" className="flex items-center gap-3 group">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--gold-primary)] to-[var(--gold-dark)] flex items-center justify-center shadow-lg group-hover:shadow-[var(--shadow-gold)] transition-shadow">
                        <Scale className="w-5 h-5 text-[#0d1117]" />
                    </div>
                    <span className="text-xl font-bold gradient-text">LegalOps AI</span>
                </Link>
                <div className="flex items-center gap-4">
                    <Link href="/research" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-sm font-medium">
                        Research
                    </Link>
                    <Link href="/dashboard" className="btn-primary px-6 py-2.5 text-sm">
                        Launch App
                    </Link>
                </div>
            </nav>

            <div className="flex-1 flex flex-col items-center justify-center px-4 py-24 relative z-10">
                <div className="max-w-5xl mx-auto text-center space-y-8">
                    <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-[var(--border-medium)] bg-[var(--bg-card)] backdrop-blur-xl text-sm font-medium animate-fade-in">
                        <Sparkles className="w-4 h-4 text-[var(--gold-primary)]" />
                        <span className="gradient-text">Powered by Advanced AI</span>
                        <span className="text-[var(--text-tertiary)]">•</span>
                        <span className="text-[var(--emerald)]">v2.0 Now Live</span>
                    </div>

                    <h1 className="text-6xl md:text-8xl font-bold tracking-tight leading-[0.95] animate-slide-up">
                        <span className="text-[var(--text-primary)]">Malaysian Legal</span>
                        <br />
                        <span className="gradient-text">Intelligence</span>
                    </h1>

                    <p className="text-xl md:text-2xl text-[var(--text-secondary)] max-w-3xl mx-auto font-light leading-relaxed animate-slide-up stagger-1">
                        A sophisticated multi-agent system for legal document processing, 
                        <span className="text-[var(--teal-primary)]"> bilingual drafting</span>, and 
                        <span className="text-[var(--gold-primary)]"> comprehensive research</span>.
                    </p>

                    <div className="flex flex-col md:flex-row items-center justify-center gap-6 pt-6 animate-slide-up stagger-2">
                        <Link
                            href="/dashboard"
                            className="group btn-primary flex items-center gap-3 text-lg px-10 py-5"
                        >
                            <Zap className="w-5 h-5" />
                            <span>Launch Command Center</span>
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link
                            href="/research"
                            className="btn-secondary flex items-center gap-3 text-lg px-10 py-5"
                        >
                            <Search className="w-5 h-5" />
                            <span>Explore Research</span>
                        </Link>
                    </div>

                    <div className="flex items-center justify-center gap-8 pt-8 text-sm text-[var(--text-tertiary)] animate-fade-in stagger-3">
                        <div className="flex items-center gap-2">
                            <Shield className="w-4 h-4 text-[var(--emerald)]" />
                            <span>Enterprise Security</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Globe className="w-4 h-4 text-[var(--teal-primary)]" />
                            <span>Bilingual Support</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Brain className="w-4 h-4 text-[var(--gold-primary)]" />
                            <span>Multi-Agent AI</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="relative z-10 py-32 px-4">
                <div className="cyber-line mb-16"></div>
                <div className="container mx-auto max-w-7xl">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl md:text-5xl font-bold gradient-text mb-4">Core Capabilities</h2>
                        <p className="text-[var(--text-secondary)] text-lg max-w-2xl mx-auto">
                            Cutting-edge AI agents working in harmony to transform your legal practice
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        <Link href="/dashboard" className="group">
                            <div className="glass-card h-full flex flex-col p-10 hover:border-[var(--gold-primary)]/40 transition-all duration-300">
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--gold-primary)] to-[var(--gold-dark)] flex items-center justify-center mb-8 shadow-lg group-hover:shadow-[var(--shadow-gold)] group-hover:scale-105 transition-all duration-300">
                                    <FileText className="w-8 h-8 text-[#0d1117]" />
                                </div>
                                <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4 group-hover:gradient-text transition-all">
                                    Matter Command
                                </h2>
                                <p className="text-[var(--text-secondary)] leading-relaxed flex-1">
                                    Comprehensive management with intelligent risk scoring, automated triage, and parallel document viewing capabilities.
                                </p>
                                <div className="flex items-center gap-2 mt-6 text-[var(--gold-primary)] font-medium">
                                    <span>Explore</span>
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>
                        </Link>

                        <Link href="/drafting" className="group">
                            <div className="glass-card h-full flex flex-col p-10 hover:border-[var(--teal-primary)]/40 transition-all duration-300">
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--teal-primary)] to-[var(--teal-dark)] flex items-center justify-center mb-8 shadow-lg group-hover:shadow-[var(--shadow-teal)] group-hover:scale-105 transition-all duration-300">
                                    <Scale className="w-8 h-8 text-white" />
                                </div>
                                <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4 group-hover:gradient-text-teal transition-all">
                                    Bilingual Drafting
                                </h2>
                                <p className="text-[var(--text-secondary)] leading-relaxed flex-1">
                                    Generate formal pleadings in Malay with synchronized English companion drafts using advanced AI templates.
                                </p>
                                <div className="flex items-center gap-2 mt-6 text-[var(--teal-primary)] font-medium">
                                    <span>Explore</span>
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>
                        </Link>

                        <Link href="/research" className="group">
                            <div className="glass-card h-full flex flex-col p-10 hover:border-[var(--emerald)]/40 transition-all duration-300">
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--emerald)] to-[#059669] flex items-center justify-center mb-8 shadow-lg group-hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] group-hover:scale-105 transition-all duration-300">
                                    <Search className="w-8 h-8 text-white" />
                                </div>
                                <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4 group-hover:text-[var(--emerald)] transition-all">
                                    Legal Research
                                </h2>
                                <p className="text-[var(--text-secondary)] leading-relaxed flex-1">
                                    Deep search across Malaysian caselaw with bilingual headnotes and comprehensive authority classification.
                                </p>
                                <div className="flex items-center gap-2 mt-6 text-[var(--emerald)] font-medium">
                                    <span>Explore</span>
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>
                        </Link>
                    </div>
                </div>
            </div>

            <footer className="relative z-10 py-12 text-center border-t border-[var(--border-light)]">
                <div className="flex items-center justify-center gap-3 text-[var(--text-tertiary)] text-sm">
                    <div className="w-2 h-2 rounded-full bg-[var(--emerald)] animate-pulse"></div>
                    <span>All systems operational</span>
                    <span className="mx-2">•</span>
                    <span>&copy; 2025 Malaysian Legal AI Agent</span>
                </div>
            </footer>
        </main>
    )
}