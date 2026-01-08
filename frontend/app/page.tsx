'use client'

import Link from 'next/link'
import Image from 'next/image'
import { Scale, MapPin, ArrowRight, Lock, Globe, Shield, Activity, Users } from 'lucide-react'

export default function Home() {
    return (
        <div className="min-h-screen bg-white text-black font-sans selection:bg-[#D4A853] selection:text-black flex flex-col">
            {/* Header */}
            <header className="w-full z-50 bg-black text-white h-20 fixed top-0 border-b border-white/10">
                <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-serif font-black tracking-widest uppercase">LegalOps</span>
                        <span className="px-2 py-0.5 bg-white/10 text-[10px] font-bold uppercase tracking-wider rounded-sm">Global</span>
                    </div>
                    <div className="hidden md:flex items-center gap-8 text-sm font-bold tracking-widest uppercase text-gray-400">
                        <Link href="#jurisdictions" className="hover:text-white transition-colors">Jurisdictions</Link>
                        <Link href="#features" className="hover:text-white transition-colors">Capabilities</Link>
                        <Link href="#enterprise" className="hover:text-white transition-colors">Enterprise</Link>
                    </div>
                </div>
            </header>

            {/* Global Hero Section - Split Layout with Image */}
            <main className="flex-1 w-full pt-20">
                <section className="relative px-6 py-20 bg-white overflow-hidden">
                    <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                        {/* Left Content */}
                        <div className="relative z-10">
                            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-black/10 bg-gray-50 mb-8">
                                <Globe className="w-4 h-4 text-[#D4A853]" />
                                <span className="text-xs font-bold tracking-wide uppercase text-gray-600">Multi-Jurisdictional AI</span>
                            </div>

                            <h1 className="text-5xl md:text-7xl font-serif font-black mb-8 leading-[0.9] tracking-tight uppercase text-black">
                                Legal <br />
                                <span className="text-[#D4A853]">Intelligence</span> <br />
                                Global Scale
                            </h1>

                            <p className="text-xl text-gray-600 max-w-lg mb-12 font-light leading-relaxed">
                                The first AI platform engineered to understand the specific nuance of local legislation, case law, and procedural rules across multiple jurisdictions.
                            </p>

                            <div className="flex flex-col sm:flex-row items-start gap-6">
                                <a href="#jurisdictions" className="px-8 py-4 bg-[#D4A853] text-black font-bold uppercase tracking-widest text-sm hover:bg-[#E8C775] transition-all shadow-xl hover:shadow-2xl">
                                    Select Region
                                </a>
                            </div>
                        </div>

                        {/* Right Image - Scales (Like 'The Old One' / Malaysia Page) */}
                        <div className="relative h-[600px] w-full">
                            {/* Decorative Elements */}
                            <div className="absolute top-10 right-10 w-full h-full border-4 border-[#D4A853] rounded-3xl -z-10 translate-x-4 translate-y-4"></div>

                            <div className="relative h-full w-full rounded-3xl overflow-hidden shadow-2xl">
                                <img
                                    src="/hero-scales.jpg"
                                    alt="Global Legal Operations"
                                    className="absolute inset-0 w-full h-full object-cover"
                                />
                                {/* Gradient Overlay */}
                                <div className="absolute inset-0 bg-black/10"></div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Jurisdiction Selector Section (The Cards) */}
                <section id="jurisdictions" className="py-24 bg-gray-50 relative border-t border-gray-200">
                    <div className="max-w-7xl mx-auto px-6">
                        <div className="text-center mb-16">
                            <h2 className="text-4xl md:text-5xl font-serif font-black mb-4 uppercase">Select Jurisdiction</h2>
                            <div className="h-1 w-24 bg-[#D4A853] mx-auto"></div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 h-[500px]">
                            {/* Malaysia Card (Active) */}
                            <Link href="/my" className="group relative h-full w-full overflow-hidden rounded-sm shadow-2xl hover:shadow-3xl transition-all duration-500 hover:-translate-y-2">
                                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1596422846543-75c6fc197f07?q=80&w=1000&auto=format&fit=crop')] bg-cover bg-center transition-transform duration-700 group-hover:scale-110"></div>
                                <div className="absolute inset-0 bg-black/60 group-hover:bg-black/40 transition-colors duration-500"></div>
                                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent"></div>

                                <div className="relative h-full p-8 flex flex-col justify-end">
                                    <div className="absolute top-6 right-6">
                                        <span className="px-3 py-1 bg-[#D4A853] text-black text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                                            <div className="w-2 h-2 bg-black rounded-full animate-pulse"></div>
                                            Online
                                        </span>
                                    </div>

                                    <div className="border-l-4 border-[#D4A853] pl-6 mb-4 transform translate-y-4 group-hover:translate-y-0 transition-transform duration-500">
                                        <h2 className="text-4xl font-serif font-black text-white uppercase mb-2">Malaysia</h2>
                                        <p className="text-gray-200 text-sm font-medium leading-relaxed opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-100">
                                            Specialized AI for Malaysian Civil & Criminal Law. Bilingual Support.
                                        </p>
                                    </div>

                                    <div className="flex items-center gap-3 text-[#D4A853] font-bold text-sm tracking-widest uppercase transform translate-y-8 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-500 delay-200">
                                        Enter Portal <ArrowRight className="w-4 h-4" />
                                    </div>
                                </div>
                            </Link>

                            {/* USA Card (Coming Soon) */}
                            <div className="group relative h-full w-full overflow-hidden rounded-sm shadow-lg grayscale hover:grayscale-0 transition-all duration-500">
                                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1501594907352-04cda38ebc29?q=80&w=1000&auto=format&fit=crop')] bg-cover bg-center transition-transform duration-700 group-hover:scale-110"></div>
                                <div className="absolute inset-0 bg-black/70 group-hover:bg-black/50 transition-colors duration-500"></div>
                                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>

                                <div className="relative h-full p-8 flex flex-col justify-end">
                                    <div className="absolute top-6 right-6">
                                        <span className="px-3 py-1 bg-white/10 text-gray-300 text-xs font-bold uppercase tracking-wider backdrop-blur-sm flex items-center gap-2 border border-white/10">
                                            <Lock className="w-3 h-3" />
                                            Coming Soon
                                        </span>
                                    </div>

                                    <div className="border-l-4 border-gray-600 pl-6 mb-4">
                                        <h2 className="text-4xl font-serif font-black text-gray-400 uppercase mb-2 group-hover:text-white transition-colors">USA</h2>
                                        <p className="text-gray-400 text-sm font-medium leading-relaxed group-hover:text-gray-200 transition-colors">
                                            Federal & State Law Integration.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* India Card (Coming Soon) */}
                            <div className="group relative h-full w-full overflow-hidden rounded-sm shadow-lg grayscale hover:grayscale-0 transition-all duration-500">
                                <div className="absolute inset-0 bg-[url('/india-gate.png')] bg-cover bg-center transition-transform duration-700 group-hover:scale-110"></div>
                                <div className="absolute inset-0 bg-black/50 group-hover:bg-black/30 transition-colors duration-500"></div>
                                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>

                                <div className="relative h-full p-8 flex flex-col justify-end">
                                    <div className="absolute top-6 right-6">
                                        <span className="px-3 py-1 bg-white/10 text-gray-300 text-xs font-bold uppercase tracking-wider backdrop-blur-sm flex items-center gap-2 border border-white/10">
                                            <Lock className="w-3 h-3" />
                                            Coming Soon
                                        </span>
                                    </div>

                                    <div className="border-l-4 border-gray-600 pl-6 mb-4">
                                        <h2 className="text-4xl font-serif font-black text-gray-400 uppercase mb-2 group-hover:text-white transition-colors">India</h2>
                                        <p className="text-gray-400 text-sm font-medium leading-relaxed group-hover:text-gray-200 transition-colors">
                                            IPC, CrPC, & Constitution Support.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Capabilities Section */}
                <section id="features" className="py-24 bg-gray-50">
                    <div className="max-w-7xl mx-auto px-6">
                        <div className="text-center mb-16">
                            <h2 className="text-4xl md:text-5xl font-serif font-black uppercase mb-4">
                                AI-Powered <span className="text-[#D4A853]">Capabilities</span>
                            </h2>
                            <p className="text-gray-600 max-w-2xl mx-auto">
                                Advanced legal automation built for modern law practices
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <div className="bg-white p-8 rounded-lg border border-gray-200 hover:border-[#D4A853] transition-all">
                                <div className="w-12 h-12 bg-[#D4A853] rounded-lg flex items-center justify-center mb-6">
                                    <Scale className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="text-xl font-bold uppercase mb-4">Intelligent Drafting</h3>
                                <p className="text-gray-600 text-sm leading-relaxed">
                                    AI-powered bilingual legal document generation with jurisdiction-specific templates and automated citation
                                </p>
                            </div>

                            <div className="bg-white p-8 rounded-lg border border-gray-200 hover:border-[#D4A853] transition-all">
                                <div className="w-12 h-12 bg-[#D4A853] rounded-lg flex items-center justify-center mb-6">
                                    <Globe className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="text-xl font-bold uppercase mb-4">Legal Research</h3>
                                <p className="text-gray-600 text-sm leading-relaxed">
                                    Search across multiple jurisdictions with AI-powered case law analysis and bilingual headnotes
                                </p>
                            </div>

                            <div className="bg-white p-8 rounded-lg border border-gray-200 hover:border-[#D4A853] transition-all">
                                <div className="w-12 h-12 bg-[#D4A853] rounded-lg flex items-center justify-center mb-6">
                                    <Shield className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="text-xl font-bold uppercase mb-4">Case Management</h3>
                                <p className="text-gray-600 text-sm leading-relaxed">
                                    Comprehensive matter tracking with AI-powered risk assessment and automated workflow orchestration
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Enterprise Section */}
                <section id="enterprise" className="py-24 bg-white border-t border-gray-200">
                    <div className="max-w-7xl mx-auto px-6">
                        <div className="text-center mb-16">
                            <h2 className="text-4xl md:text-5xl font-serif font-black uppercase mb-4">
                                Built for <span className="text-[#D4A853]">Enterprise</span>
                            </h2>
                            <p className="text-gray-600 max-w-2xl mx-auto">
                                Scalable, secure, and reliable legal infrastructure for global law firms and legal departments
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
                            <div>
                                <div className="w-16 h-16 bg-black text-[#D4A853] rounded-full flex items-center justify-center mx-auto mb-6">
                                    <Shield className="w-8 h-8" />
                                </div>
                                <h3 className="text-xl font-bold uppercase mb-2">Enterprise Security</h3>
                                <p className="text-gray-500 text-sm">ISO 27001 Certified, SOC 2 Type II Compliant, Bank-Grade Encryption</p>
                            </div>
                            <div>
                                <div className="w-16 h-16 bg-black text-[#D4A853] rounded-full flex items-center justify-center mx-auto mb-6">
                                    <Activity className="w-8 h-8" />
                                </div>
                                <h3 className="text-xl font-bold uppercase mb-2">99.99% Uptime SLA</h3>
                                <p className="text-gray-500 text-sm">Enterprise-Grade Infrastructure with 24/7 Dedicated Support</p>
                            </div>
                            <div>
                                <div className="w-16 h-16 bg-black text-[#D4A853] rounded-full flex items-center justify-center mx-auto mb-6">
                                    <Users className="w-8 h-8" />
                                </div>
                                <h3 className="text-xl font-bold uppercase mb-2">Trusted Globally</h3>
                                <p className="text-gray-500 text-sm">Serving 500+ Law Firms, Legal Teams & Corporate Counsels Worldwide</p>
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            <footer className="bg-[#0a0a0a] text-white p-12 mt-auto border-t border-[#D4A853]/30">
                <div className="max-w-7xl mx-auto px-6 text-center">
                    <span className="text-2xl font-serif font-black tracking-widest uppercase block mb-4">LegalOps Global</span>
                    <p className="text-gray-400 text-xs uppercase tracking-widest">
                        © 2024 ApexNeural Legal Ops. All rights reserved.
                    </p>
                </div>
            </footer>
        </div>
    )
}
