'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Scale, Shield, ArrowRight, Brain, FileText, Search, Gavel, CheckCircle2, Languages, MessageSquare, BookOpen, Bot, Star, ChevronDown } from 'lucide-react'

// Content Definitions for Translation
const content = {
    en: {
        nav: {
            home: "Home",
            about: "About",
            features: "Features",
            contact: "Contact",
            signIn: "Sign In",
            getStarted: "Get Started"
        },
        hero: {
            badge: "Malaysia Edition",
            title: "Legal Intelligence",
            subtitle: "Redefined",
            description: "The first AI associate engineered specifically for the Malaysian legal system. Analysis, drafting, and research at superhuman speed.",
            cta: "Access Platform"
        },
        paralegal: {
            title: "Your Digital Associate",
            subtitle: "What We Do For You",
            description: "Let your AI handle the heavy lifting while you focus on winning cases.",
            cards: [
                {
                    title: "Document Summaries",
                    desc: "Upload any legal documents - we'll read everything and give you a clear summary with key dates and facts organized for you."
                },
                {
                    title: "Case Law Search",
                    desc: "Tell us what you're looking for. We'll search through thousands of Malaysian court cases and show you the most relevant ones."
                },
                {
                    title: "Draft Documents",
                    desc: "Need a legal document? Just tell us what you need - we'll write it in English or Bahasa Malaysia, perfectly formatted."
                },
                {
                    title: "Evidence Organization",
                    desc: "Upload all your case files. We'll organize everything into a proper hearing bundle with page numbers and an index."
                },
                {
                    title: "Case Strategy",
                    desc: "Get insights on your case strengths and weaknesses. We analyze similar past cases to help you build winning arguments."
                },
                {
                    title: "24/7 Legal Chat",
                    desc: "Ask any legal question anytime. Your AI assistant remembers your cases and gives you instant, helpful answers."
                }
            ]
        }
    },
    bm: {
        nav: {
            home: "Utama",
            about: "Tentang",
            features: "Ciri",
            contact: "Hubungi",
            signIn: "Log Masuk",
            getStarted: "Mula"
        },
        hero: {
            badge: "Edisi Malaysia",
            title: "Kepintaran Legal",
            subtitle: "Didefinisi Semula",
            description: "Sekutu AI pertama yang direka khusus untuk sistem perundangan Malaysia. Analisis, draf, dan penyelidikan pada kelajuan luar biasa.",
            cta: "Akses Platform"
        },
        paralegal: {
            title: "Sekutu Digital Anda",
            subtitle: "Apa Yang Kami Tawarkan",
            description: "Biarkan AI anda menguruskan kerja berat sementara anda fokus memenangi kes.",
            cards: [
                {
                    title: "Ringkasan Dokumen",
                    desc: "Muat naik sebarang dokumen undang-undang - kami akan baca semuanya dan berikan ringkasan jelas dengan tarikh dan fakta penting yang tersusun."
                },
                {
                    title: "Carian Kes Mahkamah",
                    desc: "Beritahu kami apa yang anda cari. Kami akan mencari beribu-ribu kes mahkamah Malaysia dan tunjukkan yang paling relevan."
                },
                {
                    title: "Draf Dokumen",
                    desc: "Perlukan dokumen undang-undang? Beritahu sahaja keperluan anda - kami akan tulis dalam Inggeris atau BM dengan format sempurna."
                },
                {
                    title: "Susun Bukti",
                    desc: "Muat naik semua fail kes anda. Kami akan susun semuanya menjadi ikatan perbicaraan yang lengkap dengan nombor halaman dan indeks."
                },
                {
                    title: "Strategi Kes",
                    desc: "Dapatkan pandangan mengenai kekuatan dan kelemahan kes anda. Kami menganalisis kes lepas yang serupa untuk membantu anda membina hujah yang mantap."
                },
                {
                    title: "Chat Legal 24/7",
                    desc: "Tanya sebarang soalan undang-undang pada bila-bila masa. Pembantu AI anda mengingati kes anda dan memberikan jawapan segera."
                }
            ]
        }
    }
}

export default function MalaysiaLandingPage() {
    const [lang, setLang] = useState<'en' | 'bm'>('en')
    const t = content[lang]

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-[#D4A853] selection:text-white">

            {/* Transparent Header */}
            <header className="fixed w-full z-50 top-0 left-0 border-b border-white/10 bg-black/50 backdrop-blur-md transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 group">
                        <div className="w-8 h-8 bg-[#D4A853] rounded-full flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                            <Scale className="w-4 h-4" />
                        </div>
                        <span className="text-xl font-serif font-black tracking-widest uppercase">LegalOps</span>
                        <span className="text-[10px] font-bold border border-[#D4A853] text-[#D4A853] px-1.5 py-0.5 rounded-xl">MY</span>
                    </Link>

                    <div className="flex items-center gap-6 text-xs font-bold tracking-widest uppercase">
                        <button
                            onClick={() => setLang(lang === 'en' ? 'bm' : 'en')}
                            className="flex items-center gap-2 text-[#D4A853] hover:text-white transition-colors"
                        >
                            <Languages className="w-3 h-3" />
                            {lang === 'en' ? 'BM' : 'EN'}
                        </button>

                        <Link href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                            <span className="hidden md:inline">Switch Region</span>
                        </Link>

                        <div className="flex items-center gap-4 ml-4 pl-4 border-l border-white/20">
                            <Link href="/login" className="hover:text-[#D4A853] transition-colors">{t.nav.signIn}</Link>
                            <Link
                                href="/signup"
                                className="bg-slate-900 text-white hover:bg-[#D4A853] px-6 py-2.5 rounded-full transition-all"
                            >
                                {t.nav.getStarted}
                            </Link>
                        </div>
                    </div>
                </div>
            </header>

            {/* Cinematic Hero Section - Full Height */}
            <main className="relative w-full min-h-screen flex flex-col items-center justify-center overflow-hidden">
                {/* Background Image with Deep Overlay */}
                <div className="absolute inset-0 z-0">
                    <img
                        src="/hero-scales.jpg"
                        alt="Background"
                        className="absolute inset-0 w-full h-full object-cover opacity-40 scale-105 animate-slow-pan"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/80 to-transparent"></div>
                    <div className="absolute inset-0 bg-black/40"></div>
                </div>

                {/* Hero Content - Centered & Bold */}
                <div className="relative z-10 text-center px-6 max-w-5xl mx-auto space-y-8 pt-20">
                    <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full border border-[#D4A853]/30 bg-[#D4A853]/10 backdrop-blur-sm mb-4 animate-fade-in-up">
                        <Star className="w-3 h-3 text-[#D4A853]" fill="#D4A853" />
                        <span className="text-[#D4A853] text-[10px] font-bold tracking-[0.3em] uppercase">{t.hero.badge}</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-serif font-black leading-none tracking-tighter uppercase mix-blend-overlay opacity-90 animate-fade-in-up delay-100">
                        MALAYSIA <br /> LEGAL INTELLIGENCE
                    </h1>
                    <h1 className="text-5xl md:text-7xl font-serif font-black leading-none tracking-tighter uppercase text-transparent bg-clip-text bg-gradient-to-b from-[#D4A853] to-[#8a6c25] -mt-2 md:-mt-4 animate-fade-in-up delay-200">
                        {t.hero.subtitle}
                    </h1>

                    <p className="text-gray-300 text-lg md:text-xl max-w-xl mx-auto font-light leading-relaxed animate-fade-in-up delay-300">
                        {t.hero.description}
                    </p>

                    {/* Features List - "Incorporate Paralegal Agent Features" in Hero */}
                    <div className="flex flex-wrap justify-center gap-3 animate-fade-in-up delay-400 mt-8 max-w-3xl mx-auto">
                        {['Document Summaries', 'Case Law Search', 'Draft Documents', 'Evidence Bundle', 'Case Strategy', 'AI Legal Chat'].map((feature, i) => (
                            <div key={i} className="flex items-center gap-2 px-5 py-2 rounded-full border border-[#D4A853]/30 bg-black/40 backdrop-blur-sm shadow-[0_0_10px_rgba(212,168,83,0.1)] hover:bg-[#D4A853]/10 transition-colors cursor-default">
                                <CheckCircle2 className="w-3 h-3 text-[#D4A853]" />
                                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-200">{feature}</span>
                            </div>
                        ))}
                    </div>

                    <div className="pt-8 flex flex-col items-center gap-6 animate-fade-in-up delay-500">
                        <Link
                            href="/signup"
                            className="bg-[#D4A853] text-white px-10 py-5 rounded-full font-bold text-sm tracking-[0.2em] uppercase hover:bg-slate-900 hover:text-white hover:scale-105 transition-all duration-300 shadow-[0_0_40px_rgba(212,168,83,0.3)]"
                        >
                            {t.hero.cta}
                        </Link>

                        <div className="animate-bounce mt-10 text-gray-500">
                            <ChevronDown className="w-6 h-6" />
                        </div>
                    </div>
                </div>
            </main>

            {/* Content Section - Dark Minimalist */}
            <section className="bg-[#050505] py-32 px-6 relative z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col md:flex-row justify-between items-end mb-20 border-b border-white/10 pb-8">
                        <div>
                            <span className="text-[#D4A853] font-bold tracking-widest uppercase text-xs mb-4 block">{t.paralegal.subtitle}</span>
                            <h2 className="text-4xl md:text-6xl font-serif font-black">{t.paralegal.title}</h2>
                        </div>
                        <p className="text-gray-400 text-sm max-w-xs text-right mt-4 md:mt-0">
                            {t.paralegal.description}
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {t.paralegal.cards.map((card, idx) => (
                            <div key={idx} className="group relative bg-[#0a0a0a] border border-white/5 p-8 rounded-2xl hover:border-[#D4A853]/50 transition-all duration-500 hover:-translate-y-2 overflow-hidden">
                                <div className="absolute inset-0 bg-gradient-to-br from-[#D4A853]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                                <div className="relative z-10">
                                    <div className="w-12 h-12 bg-black border border-white/10 rounded-full flex items-center justify-center mb-6 group-hover:border-[#D4A853] transition-colors">
                                        <span className="text-[#D4A853] font-serif font-bold text-lg">{idx + 1}</span>
                                    </div>
                                    <h3 className="text-2xl font-serif font-bold mb-3 text-white">{card.title}</h3>
                                    <p className="text-gray-400 text-sm leading-relaxed group-hover:text-gray-200 transition-colors">
                                        {card.desc}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <footer className="bg-[#050505] text-white py-12 border-t border-white/5">
                <div className="max-w-7xl mx-auto px-6 text-center">
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest">Designed in Kuala Lumpur</span>
                </div>
            </footer>

            {/* Custom Animations (Tailwind config might exist, but using standard classes mostly) */}
            <style jsx global>{`
                @keyframes slow-pan {
                    0% { transform: scale(1.05); }
                    100% { transform: scale(1.1); }
                }
                .animate-slow-pan {
                    animation: slow-pan 20s alternate infinite ease-in-out;
                }
            `}</style>
        </div>
    )
}
