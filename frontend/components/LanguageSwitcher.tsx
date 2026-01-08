'use client'

import { useLanguage } from '@/lib/LanguageContext'
import { Globe, ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

export function LanguageSwitcher() {
    const { language, setLanguage, t } = useLanguage()
    const [isOpen, setIsOpen] = useState(false)
    const dropdownRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const currentLabel = language === 'en' ? 'EN' : 'BM'

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-[var(--border-light)] bg-[var(--bg-card)] hover:border-[var(--border-medium)] transition-all text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                aria-label="Select language"
            >
                <Globe className="w-4 h-4" />
                <span>{currentLabel}</span>
                <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute right-0 top-full mt-2 w-44 py-2 rounded-xl border border-[var(--border-light)] bg-[var(--bg-secondary)] shadow-lg backdrop-blur-xl z-50">
                    <button
                        onClick={() => { setLanguage('en'); setIsOpen(false) }}
                        className={`w-full px-4 py-2.5 text-left text-sm hover:bg-[var(--bg-tertiary)] transition-colors flex items-center gap-3 ${language === 'en' ? 'text-[var(--gold-primary)]' : 'text-[var(--text-secondary)]'
                            }`}
                    >
                        <span className="text-base">🇬🇧</span>
                        <span>{t.language.english}</span>
                    </button>
                    <button
                        onClick={() => { setLanguage('ms'); setIsOpen(false) }}
                        className={`w-full px-4 py-2.5 text-left text-sm hover:bg-[var(--bg-tertiary)] transition-colors flex items-center gap-3 ${language === 'ms' ? 'text-[var(--gold-primary)]' : 'text-[var(--text-secondary)]'
                            }`}
                    >
                        <span className="text-base">🇲🇾</span>
                        <span>{t.language.malay}</span>
                    </button>
                </div>
            )}
        </div>
    )
}
