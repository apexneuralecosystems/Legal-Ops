'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import en from './i18n/en.json'
import ms from './i18n/ms.json'

type Language = 'en' | 'ms'
type Translations = typeof en

interface LanguageContextType {
    language: Language
    setLanguage: (lang: Language) => void
    t: Translations
}

const translations: Record<Language, Translations> = { en, ms }

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [language, setLanguageState] = useState<Language>('en')
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
        const saved = localStorage.getItem('legalops-language') as Language
        if (saved && (saved === 'en' || saved === 'ms')) {
            setLanguageState(saved)
        }
    }, [])

    const setLanguage = (lang: Language) => {
        setLanguageState(lang)
        localStorage.setItem('legalops-language', lang)
    }

    const t = translations[language]

    // Prevent hydration mismatch by returning English during SSR
    if (!mounted) {
        return (
            <LanguageContext.Provider value={{ language: 'en', setLanguage, t: en }}>
                {children}
            </LanguageContext.Provider>
        )
    }

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    )
}

export function useLanguage() {
    const context = useContext(LanguageContext)
    if (!context) {
        throw new Error('useLanguage must be used within a LanguageProvider')
    }
    return context
}
