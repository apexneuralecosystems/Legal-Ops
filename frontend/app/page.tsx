'use client'

import Link from 'next/link'
import { Scale, Sparkles, ArrowRight, Lock, Globe, Shield, Activity, Users, Gavel, BookOpen, FileText, Search } from 'lucide-react'

export default function Home() {
    return (
        <div className="min-h-screen relative z-10 flex flex-col">
            {/* Legal Pattern Background */}
            <div className="fixed inset-0 z-0 grid-pattern opacity-20" />

            {/* Professional Header */}
            <header className="w-full z-50 fixed top-0 backdrop-blur-sm bg-slate-900/90 border-b border-[#D4A853]/20 font-serif">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="w-11 h-11 bg-gradient-to-br from-[#D4A853] to-[#B88A3E] flex items-center justify-center shadow-lg border border-[#D4A853]/30">
                            <Scale className="w-6 h-6 text-black" />
                        </div>
                        <div>
                            <span className="text-2xl font-bold gradient-text font-serif">LegalOps</span>
                            <div className="text-[9px] text-[#D4A853] tracking-[0.25em] font-semibold uppercase">Legal Intelligence</div>
                        </div>
                    </Link>
                    <nav className="hidden md:flex items-center gap-8">
                        <Link href="#jurisdictions" className="text-sm font-semibold text-white hover:text-[#D4A853] transition-colors uppercase tracking-wide">
                            Jurisdictions
                        </Link>
                        <Link href="#features" className="text-sm font-semibold text-white hover:text-[#D4A853] transition-colors uppercase tracking-wide">
                            Practice Areas
                        </Link>
                        <Link href="#enterprise" className="text-sm font-semibold text-white hover:text-[#D4A853] transition-colors uppercase tracking-wide">
                            Firms
                        </Link>
                        <Link href="/my" className="px-6 py-2.5 bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-white text-sm font-bold uppercase tracking-wider rounded-lg hover:from-[#E8C775] hover:to-[#D4A853] transition-all shadow-lg border border-[#D4A853]/50">
                            Client Portal
                        </Link>
                    </nav>
                </div>
            </header>

            {/* Hero Section */}
            <main className="flex-1 w-full pt-20 relative z-10 font-serif">
                <section className="relative px-6 py-32 overflow-hidden bg-gradient-to-b from-black to-[#0A0A0A]">
                    <div className="max-w-7xl mx-auto">
                        <div className="text-center mb-16 animate-fadeIn">
                            {/* Legal Badge */}
                            <div className="inline-flex items-center gap-3 px-6 py-3 glass-card mb-8 border border-[#D4A853]/30">
                                <div className="w-6 h-6 bg-gradient-to-br from-[#D4A853] to-[#B88A3E] flex items-center justify-center border border-[#D4A853]/30">
                                    <Gavel className="w-4 h-4 text-black" />
                                </div>
                                <span className="text-[#D4A853] text-sm font-serif font-bold tracking-wide">Est. 2024 • AI-Powered Legal Intelligence</span>
                                <div className="w-2 h-2 bg-[#D4A853] rounded-full animate-pulse" />
                            </div>

                            {/* Main Headline */}
                            <h1 className="text-6xl md:text-8xl font-serif font-bold mb-8 leading-tight">
                                <span className="gradient-text block">Premier Legal</span>
                                <span className="text-slate-100 block">Operations Platform</span>
                            </h1>

                            {/* Subheadline */}
                            <p className="text-xl md:text-2xl text-slate-300 max-w-3xl mx-auto mb-12 leading-relaxed font-serif">
                                Sophisticated AI technology serving law firms with multi-jurisdictional expertise in legislation, case law, and procedural practice.
                            </p>

                            {/* CTA Buttons */}
                            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                                <a href="#jurisdictions" className="px-8 py-4 bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-white font-serif font-bold uppercase tracking-wider rounded-xl hover:from-[#E8C775] hover:to-[#D4A853] transition-all shadow-lg shadow-[#D4A853]/30 border border-[#D4A853]/50 group">
                                    Select Jurisdiction
                                    <ArrowRight className="w-5 h-5 inline-block ml-2 group-hover:translate-x-1 transition-transform" />
                                </a>
                                <Link href="/my" className="px-8 py-4 border-2 border-[#D4A853] font-serif font-bold uppercase tracking-wider rounded-xl text-[#D4A853] hover:bg-[#D4A853] hover:text-white transition-all">
                                    Client Access
                                </Link>
                            </div>
                        </div>

                        {/* Feature Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24">
                            {[
                                { icon: BookOpen, title: 'AI Legal Research', desc: 'Find relevant cases instantly. Our AI searches millions of legal documents and gives you the answers you need in seconds.' },
                                { icon: FileText, title: 'Smart Document Drafting', desc: 'Create professional legal documents in minutes. Our AI handles formatting, citations, and even multiple languages.' },
                                { icon: Gavel, title: 'Case Strategy Insights', desc: 'Know your case strengths before court. Our AI analyzes similar cases to help you build winning strategies.' }
                            ].map((feature, i) => (
                                <div key={i} className="glass-card p-6 hover:border-[#D4A853]/50 transition-all duration-300 group border border-[#D4A853]/20 animate-fadeIn hover:shadow-[0_0_40px_rgba(212,168,83,0.3)] hover:scale-105" style={{ animationDelay: `${i * 0.1}s` }}>
                                    <div className="w-12 h-12 bg-gradient-to-br from-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-4 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300 border border-[#D4A853]/30 shadow-lg shadow-[#D4A853]/20">
                                        <feature.icon className="w-6 h-6 text-black" />
                                    </div>
                                    <h3 className="text-xl font-serif font-bold text-[#D4A853] mb-2 group-hover:text-[#E8C775] transition-colors">{feature.title}</h3>
                                    <p className="text-slate-400 text-sm font-serif group-hover:text-slate-300 transition-colors">{feature.desc}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Jurisdiction Selector Section */}
                <section id="jurisdictions" className="py-32 px-6 relative bg-[#0F0F0F]">
                    <div className="max-w-7xl mx-auto">
                        <div className="text-center mb-20">
                            <h2 className="text-5xl md:text-6xl font-serif font-bold mb-6">
                                <span className="gradient-text">Select Your</span>
                                <span className="text-slate-100 block">Jurisdiction</span>
                            </h2>
                            <p className="text-xl text-slate-400 max-w-2xl mx-auto font-serif">
                                Specialized legal intelligence trained on regional law and practice
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                            {/* Malaysia Card (Active) */}
                            <Link href="/my" className="group relative h-[500px] premium-card spotlight overflow-hidden animate-scaleIn border-l-4 border-[#D4A853]">
                                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1596422846543-75c6fc197f07?q=80&w=1000&auto=format&fit=crop')] bg-cover bg-center transition-transform duration-700 group-hover:scale-110" />
                                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent" />

                                <div className="relative h-full p-8 flex flex-col justify-between">
                                    <div className="flex justify-end">
                                        <span className="px-4 py-2 bg-gradient-to-r from-[#D4A853] to-[#B88A3E] text-black text-xs font-serif font-bold uppercase tracking-wider flex items-center gap-2 legal-glow border border-[#D4A853]/50">
                                            <div className="w-2 h-2 bg-black rounded-full animate-pulse" />
                                            Active
                                        </span>
                                    </div>

                                    <div>
                                        <div className="mb-6 border-l-2 border-[#D4A853] pl-4">
                                            <h3 className="text-5xl font-serif font-bold text-white mb-3 group-hover:text-[#D4A853] transition-colors">
                                                Malaysia
                                            </h3>
                                            <p className="text-slate-300 leading-relaxed font-serif">
                                                Malaysian Civil & Criminal Law with bilingual support (English/Bahasa Malaysia)
                                            </p>
                                        </div>

                                        <div className="flex items-center gap-3 text-[#D4A853] font-serif font-semibold group-hover:gap-5 transition-all">
                                            Access Portal
                                            <ArrowRight className="w-5 h-5" />
                                        </div>
                                    </div>
                                </div>
                            </Link>

                            {/* USA Card (Coming Soon) */}
                            <div className="group relative h-[500px] premium-card overflow-hidden grayscale hover:grayscale-0 transition-all duration-500 animate-scaleIn" style={{ animationDelay: '100ms' }}>
                                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1501594907352-04cda38ebc29?q=80&w=1000&auto=format&fit=crop')] bg-cover bg-center transition-transform duration-700 group-hover:scale-110" />
                                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/90 to-transparent" />

                                <div className="relative h-full p-8 flex flex-col justify-between">
                                    <div className="flex justify-end">
                                        <span className="px-4 py-2 glass-card text-slate-500 text-xs font-serif font-bold uppercase tracking-wider flex items-center gap-2 border border-slate-700">
                                            <Lock className="w-3 h-3" />
                                            Coming Q3 2026
                                        </span>
                                    </div>

                                    <div>
                                        <div className="mb-6 border-l-2 border-slate-700 pl-4">
                                            <h3 className="text-5xl font-serif font-bold text-slate-600 mb-3 group-hover:text-slate-300 transition-colors">
                                                United States
                                            </h3>
                                            <p className="text-slate-600 group-hover:text-slate-400 transition-colors leading-relaxed font-serif">
                                                Federal & State Law integration across all 50 jurisdictions
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* India Card (Coming Soon) */}
                            <div className="group relative h-[500px] premium-card overflow-hidden grayscale hover:grayscale-0 transition-all duration-500 animate-scaleIn" style={{ animationDelay: '200ms' }}>
                                <div className="absolute inset-0 bg-[url('/india-gate.png')] bg-cover bg-center transition-transform duration-700 group-hover:scale-110" />
                                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/90 to-transparent" />

                                <div className="relative h-full p-8 flex flex-col justify-between">
                                    <div className="flex justify-end">
                                        <span className="px-4 py-2 glass-card text-slate-500 text-xs font-serif font-bold uppercase tracking-wider flex items-center gap-2 border border-slate-700">
                                            <Lock className="w-3 h-3" />
                                            Coming Q4 2026
                                        </span>
                                    </div>

                                    <div>
                                        <div className="mb-6 border-l-2 border-slate-700 pl-4">
                                            <h3 className="text-5xl font-serif font-bold text-slate-600 mb-3 group-hover:text-slate-300 transition-colors">
                                                India
                                            </h3>
                                            <p className="text-slate-600 group-hover:text-slate-400 transition-colors leading-relaxed font-serif">
                                                IPC, CrPC, Constitution & Supreme Court jurisprudence
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="mt-16 text-center border-t border-[#D4A853]/20 pt-8">
                            <p className="text-slate-500 text-sm font-serif">
                                Additional jurisdictions under development. <Link href="#contact" className="text-[#D4A853] hover:text-slate-400 font-semibold">Contact us</Link> for custom requirements.
                            </p>
                        </div>
                    </div>
                </section>

                {/* AI-Powered Features Section */}
                <section id="features" className="py-32 px-6 relative bg-black">
                    <div className="max-w-7xl mx-auto">
                        <div className="text-center mb-20 animate-fadeIn">
                            <div className="inline-flex items-center gap-2 px-4 py-2 glass-card mb-8 border border-[#D4A853]/30">
                                <Sparkles className="w-5 h-5 text-[#D4A853] animate-pulse" />
                                <span className="text-[#D4A853] text-sm font-serif font-bold tracking-wide">POWERED BY ADVANCED AI</span>
                            </div>
                            <h2 className="text-5xl md:text-6xl font-serif font-bold mb-6">
                                <span className="gradient-text">Revolutionary AI</span>
                                <span className="text-slate-100 block">Legal Technology</span>
                            </h2>
                            <p className="text-xl text-slate-400 max-w-3xl mx-auto font-serif leading-relaxed">
                                Harness the power of GPT-4, neural networks, and machine learning to transform your legal practice with intelligent automation
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            <div className="premium-card spotlight p-8 group hover:translate-y-[-8px] transition-all duration-500 animate-scaleIn hover:shadow-[0_20px_60px_rgba(212,168,83,0.4)]">
                                <div className="w-16 h-16 bg-gradient-to-br from-[#D4A853] via-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-6 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500 float-animation border border-[#D4A853]/30 shadow-2xl shadow-[#D4A853]/30">
                                    <Sparkles className="w-8 h-8 text-black" />
                                </div>
                                <h3 className="text-2xl font-serif font-bold text-[#D4A853] mb-4 group-hover:text-[#E8C775] transition-colors">Smart Document Scanning</h3>
                                <p className="text-slate-400 leading-relaxed font-serif group-hover:text-slate-300 transition-colors">
                                    Upload any document and our AI instantly extracts, organizes, and makes your files searchable. Turn paper into digital knowledge in seconds.
                                </p>
                                <div className="mt-6 flex items-center gap-2 text-[#D4A853] font-serif font-semibold text-sm group-hover:gap-5 transition-all">
                                    Learn More <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>

                            <div className="premium-card spotlight p-8 group hover:translate-y-[-8px] transition-all duration-500 animate-scaleIn hover:shadow-[0_20px_60px_rgba(212,168,83,0.4)]" style={{ animationDelay: '100ms' }}>
                                <div className="w-16 h-16 bg-gradient-to-br from-[#D4A853] via-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-6 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500 float-animation border border-[#D4A853]/30 shadow-2xl shadow-[#D4A853]/30">
                                    <FileText className="w-8 h-8 text-black" />
                                </div>
                                <h3 className="text-2xl font-serif font-bold text-[#D4A853] mb-4 group-hover:text-[#E8C775] transition-colors">Instant Legal Drafting</h3>
                                <p className="text-slate-400 leading-relaxed font-serif group-hover:text-slate-300 transition-colors">
                                    Create professional legal documents in minutes, not hours. Our AI writes, formats, and cites relevant cases automatically for you.
                                </p>
                                <div className="mt-6 flex items-center gap-2 text-[#D4A853] font-serif font-semibold text-sm group-hover:gap-5 transition-all">
                                    Learn More <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>

                            <div className="premium-card spotlight p-8 group hover:translate-y-[-8px] transition-all duration-500 animate-scaleIn hover:shadow-[0_20px_60px_rgba(212,168,83,0.4)]" style={{ animationDelay: '200ms' }}>
                                <div className="w-16 h-16 bg-gradient-to-br from-[#D4A853] via-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-6 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500 float-animation border border-[#D4A853]/30 shadow-2xl shadow-[#D4A853]/30">
                                    <Search className="w-8 h-8 text-black" />
                                </div>
                                <h3 className="text-2xl font-serif font-bold text-[#D4A853] mb-4 group-hover:text-[#E8C775] transition-colors">Smart Legal Search</h3>
                                <p className="text-slate-400 leading-relaxed font-serif group-hover:text-slate-300 transition-colors">
                                    Ask questions in plain English and get instant answers with supporting case references. Like having a legal researcher available 24/7.
                                </p>
                                <div className="mt-6 flex items-center gap-2 text-[#D4A853] font-serif font-semibold text-sm group-hover:gap-5 transition-all">
                                    Learn More <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>

                            <div className="premium-card spotlight p-8 group hover:translate-y-[-8px] transition-all duration-500 animate-scaleIn hover:shadow-[0_20px_60px_rgba(212,168,83,0.4)]" style={{ animationDelay: '300ms' }}>
                                <div className="w-16 h-16 bg-gradient-to-br from-[#D4A853] via-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-6 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500 float-animation border border-[#D4A853]/30 shadow-2xl shadow-[#D4A853]/30">
                                    <Activity className="w-8 h-8 text-black" />
                                </div>
                                <h3 className="text-2xl font-serif font-bold text-[#D4A853] mb-4 group-hover:text-[#E8C775] transition-colors">Case Outcome Insights</h3>
                                <p className="text-slate-400 leading-relaxed font-serif group-hover:text-slate-300 transition-colors">
                                    Understand your case strengths and risks before you step into court. Our AI analyzes patterns from thousands of similar cases to guide your strategy.
                                </p>
                                <div className="mt-6 flex items-center gap-2 text-[#D4A853] font-serif font-semibold text-sm group-hover:gap-5 transition-all">
                                    Learn More <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>

                            <div className="premium-card spotlight p-8 group hover:translate-y-[-8px] transition-all duration-500 animate-scaleIn hover:shadow-[0_20px_60px_rgba(212,168,83,0.4)]" style={{ animationDelay: '400ms' }}>
                                <div className="w-16 h-16 bg-gradient-to-br from-[#D4A853] via-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-6 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500 float-animation border border-[#D4A853]/30 shadow-2xl shadow-[#D4A853]/30">
                                    <Shield className="w-8 h-8 text-black" />
                                </div>
                                <h3 className="text-2xl font-serif font-bold text-[#D4A853] mb-4 group-hover:text-[#E8C775] transition-colors">Effortless Case Tracking</h3>
                                <p className="text-slate-400 leading-relaxed font-serif group-hover:text-slate-300 transition-colors">
                                    Never miss a deadline again. Our system automatically tracks your cases, organizes evidence, and keeps everything connected in one place.
                                </p>
                                <div className="mt-6 flex items-center gap-2 text-[#D4A853] font-serif font-semibold text-sm group-hover:gap-5 transition-all">
                                    Learn More <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>

                            <div className="premium-card spotlight p-8 group hover:translate-y-[-8px] transition-all duration-500 animate-scaleIn hover:shadow-[0_20px_60px_rgba(212,168,83,0.4)]" style={{ animationDelay: '500ms' }}>
                                <div className="w-16 h-16 bg-gradient-to-br from-[#D4A853] via-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-6 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500 float-animation border border-[#D4A853]/30 shadow-2xl shadow-[#D4A853]/30">
                                    <Users className="w-8 h-8 text-black" />
                                </div>
                                <h3 className="text-2xl font-serif font-bold text-[#D4A853] mb-4 group-hover:text-[#E8C775] transition-colors">Your Personal Legal AI</h3>
                                <p className="text-slate-400 leading-relaxed font-serif group-hover:text-slate-300 transition-colors">
                                    Chat with your AI assistant anytime. Ask questions, get document summaries, research cases, or get help drafting - it remembers your cases and learns your preferences.
                                </p>
                                <div className="mt-6 flex items-center gap-2 text-[#D4A853] font-serif font-semibold text-sm group-hover:gap-5 transition-all">
                                    Learn More <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Law Firms Section */}
                <section id="enterprise" className="py-32 px-6 relative bg-[#0F0F0F]">
                    <div className="max-w-7xl mx-auto">
                        <div className="text-center mb-20">
                            <h2 className="text-5xl md:text-6xl font-serif font-bold mb-6">
                                <span className="gradient-text">Trusted By</span>
                                <span className="text-slate-100 block">Leading Firms</span>
                            </h2>
                            <p className="text-xl text-slate-400 max-w-2xl mx-auto font-serif">
                                Enterprise-grade legal technology serving professional law firms
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
                            {[
                                { icon: Shield, title: 'Professional Security', desc: 'PDPA compliant with 256-bit encryption and secure client data handling' },
                                { icon: Activity, title: 'System Reliability', desc: '99.9% uptime guaranteed with redundant infrastructure and 24/7 monitoring' },
                                { icon: Users, title: 'Expert Support', desc: 'Dedicated account management with comprehensive training and onboarding' }
                            ].map((feature, i) => (
                                <div key={i} className="premium-card p-8 hover:translate-y-[-4px] transition-all group">
                                    <div className="w-16 h-16 bg-gradient-to-br from-[#D4A853] to-[#B88A3E] flex items-center justify-center mb-6 group-hover:scale-110 transition-transform float-animation border border-[#D4A853]/30">
                                        <feature.icon className="w-8 h-8 text-black" />
                                    </div>
                                    <h3 className="text-2xl font-serif font-bold text-[#D4A853] mb-4">{feature.title}</h3>
                                    <p className="text-slate-400 leading-relaxed font-serif">{feature.desc}</p>
                                </div>
                            ))}
                        </div>

                        <div className="glass-card p-12 text-center border border-[#D4A853]/20">
                            <div className="grid grid-cols-3 gap-8">
                                <div>
                                    <div className="text-5xl font-serif font-bold gradient-text mb-2">500+</div>
                                    <div className="text-slate-400 font-serif text-sm">Law Firms</div>
                                </div>
                                <div>
                                    <div className="text-5xl font-serif font-bold gradient-text mb-2">50K+</div>
                                    <div className="text-slate-400 font-serif text-sm">Matters</div>
                                </div>
                                <div>
                                    <div className="text-5xl font-serif font-bold gradient-text mb-2">2M+</div>
                                    <div className="text-slate-400 font-serif text-sm">Case Citations</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            {/* Professional Footer */}
            <footer className="w-full py-16 px-6 border-t border-[#D4A853]/20 bg-slate-900/50 backdrop-blur-sm font-serif">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
                        <div className="col-span-1 md:col-span-2">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-12 h-12 bg-gradient-to-br from-[#D4A853] to-[#B88A3E] flex items-center justify-center border border-[#D4A853]/30">
                                    <Scale className="w-6 h-6 text-black" />
                                </div>
                                <div>
                                    <h3 className="text-2xl font-serif font-bold gradient-text">LegalOps</h3>
                                    <p className="text-xs text-[#D4A853] tracking-widest uppercase">Legal Intelligence</p>
                                </div>
                            </div>
                            <p className="text-slate-400 leading-relaxed font-serif mb-6">
                                Premier AI-powered legal operations platform serving law firms with multi-jurisdictional expertise
                            </p>
                            <div className="flex items-center gap-4">
                                {[Globe, Shield, Activity].map((Icon, i) => (
                                    <div key={i} className="w-10 h-10 glass-card flex items-center justify-center hover:border-[#D4A853]/50 transition-all cursor-pointer group border border-[#D4A853]/20">
                                        <Icon className="w-5 h-5 text-slate-500 group-hover:text-[#D4A853] transition-colors" />
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h4 className="text-sm font-serif font-bold text-slate-300 mb-6 tracking-wide uppercase">Services</h4>
                            <ul className="space-y-3">
                                {['Legal Research', 'Document Drafting', 'Matter Management', 'Case Intelligence'].map((item, i) => (
                                    <li key={i}>
                                        <Link href="#" className="text-slate-400 hover:text-[#D4A853] transition-colors font-serif">{item}</Link>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div>
                            <h4 className="text-sm font-serif font-bold text-slate-300 mb-6 tracking-wide uppercase">Company</h4>
                            <ul className="space-y-3">
                                {['About Us', 'Contact', 'Privacy Policy', 'Terms of Service'].map((item, i) => (
                                    <li key={i}>
                                        <Link href="#" className="text-slate-400 hover:text-[#D4A853] transition-colors font-serif">{item}</Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    <div className="pt-8 border-t border-[#D4A853]/20 flex flex-col md:flex-row justify-between items-center gap-4">
                        <p className="text-slate-500 text-sm font-serif">
                            © 2024 ApexNeural LegalOps. All rights reserved.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    )
}
