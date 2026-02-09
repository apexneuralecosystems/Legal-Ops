'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    LayoutDashboard,
    Inbox,
    Search,
    FileText,
    Gavel,
    User,
    Settings,
    Scale,
    ShieldAlert
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
            { name: 'Intake', href: '/upload', icon: Inbox },
            { name: 'Research', href: '/research', icon: Search },
        ]
    },
    {
        section: 'MANAGEMENT',
        items: [
            { name: 'Matter Detail', href: '/matters', icon: FileText }, // Placeholder link
            { name: 'Drafting', href: '/drafting', icon: Scale }, // Using Scale for drafting/justice
            { name: 'Evidence', href: '/evidence', icon: Gavel }
        ]
    },
    {
        section: 'ACCOUNT',
        items: [
            { name: 'Profile', href: '/profile', icon: User },
            { name: 'Settings', href: '/settings', icon: Settings }
        ]
    }
]

export default function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="w-64 bg-[#0F0F0F] border-r border-[#C9A24D]/20 h-screen sticky top-0 flex flex-col z-20">
            {/* Brand Header */}
            <div className="h-20 flex items-center px-6 border-b border-[#C9A24D]/10">
                <div className="flex flex-col">
                    <h1 className="text-lg font-serif font-bold text-[#EAEAEA] tracking-wide flex items-center gap-2">
                        <Scale className="w-5 h-5 text-[#C9A24D]" />
                        LEGAL OPS
                    </h1>
                    <span className="text-[10px] text-[#C9A24D]/60 uppercase tracking-[0.2em] ml-7">v4.5.1</span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-8 space-y-8 overflow-y-auto custom-scrollbar">
                {navigation.map((group) => (
                    <div key={group.section} className="px-4">
                        <h3 className="px-4 mb-2 text-[10px] font-bold text-[#525252] uppercase tracking-[0.2em]">
                            {group.section}
                        </h3>
                        <ul className="space-y-1">
                            {group.items.map((item) => {
                                const isActive = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));
                                return (
                                    <li key={item.name}>
                                        <Link
                                            href={item.href}
                                            className={`
                                                relative flex items-center gap-3 px-4 py-2.5 text-xs font-medium tracking-wide rounded-md transition-all duration-200
                                                ${isActive
                                                    ? 'text-[#EAEAEA] bg-[#C9A24D]/10'
                                                    : 'text-[#9A9A9A] hover:text-[#EAEAEA] hover:bg-[#1A1A1A]'
                                                }
                                            `}
                                        >
                                            {isActive && (
                                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-[#C9A24D] shadow-[0_0_8px_rgba(201,162,77,0.5)] rounded-r-full" />
                                            )}
                                            <item.icon className={`w-4 h-4 ${isActive ? 'text-[#C9A24D]' : 'text-[#525252] group-hover:text-[#9A9A9A]'}`} />
                                            <span>{item.name}</span>
                                        </Link>
                                    </li>
                                )
                            })}
                        </ul>
                    </div>
                ))}
            </nav>

            {/* AI Status Footer */}
            <div className="p-4 border-t border-[#C9A24D]/10">
                <div className="flex items-center gap-3 px-4 py-3 bg-[#121212] border border-[#C9A24D]/10 rounded-lg">
                    <div className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-[#EAEAEA] uppercase tracking-wider">System Online</span>
                        <span className="text-[9px] text-[#525252]">Secure Connection</span>
                    </div>
                </div>
            </div>
        </aside>
    )
}