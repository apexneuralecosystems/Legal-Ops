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
            { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard }
        ]
    },
    {
        section: 'OPERATIONS',
        items: [
            { name: 'Matter Intake', href: '/upload', icon: Briefcase },
            { name: 'Pleadings', href: '/drafting', icon: FileText },
            { name: 'Research', href: '/research', icon: Search },
            { name: 'Hearings', href: '/evidence', icon: Calendar },
            { name: 'Paralegal', href: '/paralegal', icon: Sparkles }
        ]
    },
    {
        section: 'MANAGEMENT',
        items: [
            { name: 'All Matters', href: '/matters', icon: Folder },
            { name: 'Pricing', href: '/pricing', icon: CreditCard }
        ]
    }
]

export default function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="w-64 bg-black border-r border-[#D4A853]/20 h-screen sticky top-0 flex flex-col">
            {/* Logo */}
            <div className="p-5 border-b border-[#D4A853]/20">
                <Link href="/" className="flex items-center gap-2 group">
                    <div className="w-10 h-10 rounded-lg bg-[#D4A853] flex items-center justify-center text-white font-black text-xl">
                        L
                    </div>
                    <div>
                        <h2 className="text-base font-black text-white tracking-tight">LegalOps</h2>
                        <p className="text-[10px] text-white/50 tracking-widest font-bold">AI PLATFORM</p>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-4 overflow-y-auto">
                {navigation.map((section) => (
                    <div key={section.section} className="mb-6">
                        <h3 className="px-4 py-2 text-[10px] font-bold text-[#D4A853] tracking-widest">
                            {section.section}
                        </h3>
                        <ul className="space-y-0.5 px-3">
                            {section.items.map((item) => {
                                const isActive = pathname === item.href
                                return (
                                    <li key={item.name}>
                                        <Link
                                            href={item.href}
                                            className={`flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-all group ${isActive
                                                ? 'bg-[#D4A853] text-white'
                                                : 'text-gray-300 hover:bg-[#D4A853]/20 hover:text-[#E8C775]' /* Brightened from white/60 */
                                                }`}
                                        >
                                            <item.icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-[#E8C775]'}`} />
                                            <span>{item.name}</span>
                                            {isActive && <ChevronRight className="w-5 h-5 ml-auto text-white" />}
                                        </Link>
                                    </li>
                                )
                            })}
                        </ul>
                    </div>
                ))}
            </nav>

            {/* AI Status */}
            <div className="p-4 border-t border-[#D4A853]/20">
                <div className="bg-gradient-to-br from-[#D4A853]/10 to-[#D4A853]/5 border border-[#D4A853]/20 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 rounded-full bg-[#D4A853] animate-pulse"></div>
                        <span className="text-xs font-bold text-[#D4A853] tracking-wide">AI Systems Online</span>
                    </div>
                    <div className="h-1 bg-black/30 rounded-full overflow-hidden">
                        <div className="h-full w-4/5 bg-gradient-to-r from-[#D4A853] to-[#E8C775] rounded-full"></div>
                    </div>
                </div>
            </div>
        </aside>
    )
}