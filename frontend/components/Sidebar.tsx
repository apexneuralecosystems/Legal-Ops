'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    LayoutDashboard,
    Briefcase,
    FileText,
    Search,
    Calendar,
    Folder,
    Scale,
    Sparkles,
    ChevronRight,
    CreditCard
} from 'lucide-react'

const navigation = [
    {
        section: 'COMMAND',
        items: [
            { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, gradient: 'gold' }
        ]
    },
    {
        section: 'OPERATIONS',
        items: [
            { name: 'Matter Intake', href: '/upload', icon: Briefcase, gradient: 'teal' },
            { name: 'Pleadings', href: '/drafting', icon: FileText, gradient: 'gold' },
            { name: 'Research', href: '/research', icon: Search, gradient: 'teal' },
            { name: 'Hearings', href: '/evidence', icon: Calendar, gradient: 'emerald' }
        ]
    },
    {
        section: 'MANAGEMENT',
        items: [
            { name: 'All Matters', href: '/matters', icon: Folder, gradient: 'gold' },
            { name: 'Pricing', href: '/pricing', icon: CreditCard, gradient: 'emerald' }
        ]
    }
]

const gradientClasses: Record<string, string> = {
    gold: 'from-[var(--gold-primary)] to-[var(--gold-dark)]',
    teal: 'from-[var(--teal-primary)] to-[var(--teal-dark)]',
    emerald: 'from-[var(--emerald)] to-[#059669]'
}

export default function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="w-72 bg-[var(--bg-card)] backdrop-blur-xl border-r border-[var(--border-light)] h-screen sticky top-0 flex flex-col">
            <div className="p-6 border-b border-[var(--border-light)]">
                <Link href="/dashboard" className="flex items-center gap-3 group">
                    <div className="relative">
                        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[var(--gold-primary)] to-[var(--gold-dark)] flex items-center justify-center shadow-lg group-hover:shadow-[var(--shadow-gold)] transition-shadow duration-300">
                            <Scale className="w-6 h-6 text-[#0d1117]" />
                        </div>
                        <div className="absolute -top-1 -right-1 w-3 h-3">
                            <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--emerald)] opacity-75 animate-ping"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-[var(--emerald)]"></span>
                        </div>
                    </div>
                    <div>
                        <span className="text-xl font-bold gradient-text">LegalOps</span>
                        <p className="text-xs text-[var(--text-tertiary)] tracking-wider font-medium">MALAYSIAN LAW AI</p>
                    </div>
                </Link>
            </div>

            <nav className="flex-1 p-4 space-y-8 overflow-y-auto scrollbar-thin">
                {navigation.map((section) => (
                    <div key={section.section}>
                        <h3 className="text-[10px] font-bold text-[var(--text-tertiary)] tracking-[0.2em] mb-3 px-4 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-gradient-to-r from-[var(--gold-primary)] to-[var(--teal-primary)]"></span>
                            {section.section}
                        </h3>
                        <ul className="space-y-1">
                            {section.items.map((item) => {
                                const isActive = pathname === item.href
                                return (
                                    <li key={item.name}>
                                        <Link
                                            href={item.href}
                                            className={`group flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 relative overflow-hidden ${isActive
                                                    ? 'text-[#0d1117]'
                                                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                                                }`}
                                        >
                                            {isActive && (
                                                <div className={`absolute inset-0 bg-gradient-to-r ${gradientClasses[item.gradient]} opacity-90`}></div>
                                            )}
                                            {isActive && (
                                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-[#0d1117]/20"></div>
                                            )}

                                            <div className={`relative z-10 w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200 ${isActive
                                                    ? 'bg-[#0d1117]/20'
                                                    : 'bg-[var(--bg-tertiary)] group-hover:bg-[var(--bg-card)]'
                                                }`}>
                                                <item.icon className={`w-4 h-4 ${isActive ? 'text-[#0d1117]' : 'text-[var(--text-secondary)]'}`} />
                                            </div>

                                            <span className="relative z-10 flex-1">{item.name}</span>

                                            <ChevronRight className={`relative z-10 w-4 h-4 transition-all duration-200 ${isActive
                                                    ? 'opacity-100 translate-x-0'
                                                    : 'opacity-0 -translate-x-2 group-hover:opacity-50 group-hover:translate-x-0'
                                                }`} />
                                        </Link>
                                    </li>
                                )
                            })}
                        </ul>
                    </div>
                ))}
            </nav>

            <div className="p-4 border-t border-[var(--border-light)]">
                <div className="glass-card p-4 rounded-xl">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--gold-primary)] to-[var(--teal-primary)] flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-[#0d1117]" />
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-[var(--text-primary)]">AI Status</p>
                            <p className="text-xs text-[var(--text-tertiary)]">Multi-agent system</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                            <div className="h-full w-3/4 rounded-full bg-gradient-to-r from-[var(--emerald)] to-[var(--teal-primary)]"></div>
                        </div>
                        <span className="text-xs font-bold text-[var(--emerald)]">LIVE</span>
                    </div>
                </div>
            </div>
        </aside>
    )
}