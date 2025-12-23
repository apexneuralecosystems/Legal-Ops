'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import {
    Command,
    Search,
    FileText,
    Briefcase,
    PenTool,
    BookOpen,
    Upload,
    Scale,
    X,
    ArrowRight,
} from 'lucide-react'

interface CommandItem {
    id: string
    title: string
    description?: string
    icon: React.ReactNode
    action: () => void
    category: string
}

interface CommandPaletteProps {
    isOpen: boolean
    onClose: () => void
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
    const router = useRouter()
    const [query, setQuery] = useState('')
    const [selectedIndex, setSelectedIndex] = useState(0)
    const inputRef = useRef<HTMLInputElement>(null)

    const commands: CommandItem[] = [
        {
            id: 'dashboard',
            title: 'Go to Dashboard',
            description: 'View all matters and activity',
            icon: <Briefcase className="w-4 h-4" />,
            action: () => router.push('/dashboard'),
            category: 'Navigation',
        },
        {
            id: 'upload',
            title: 'Upload Documents',
            description: 'Start new intake workflow',
            icon: <Upload className="w-4 h-4" />,
            action: () => router.push('/upload'),
            category: 'Actions',
        },
        {
            id: 'drafting',
            title: 'Start Drafting',
            description: 'Create new pleading draft',
            icon: <PenTool className="w-4 h-4" />,
            action: () => router.push('/drafting'),
            category: 'Actions',
        },
        {
            id: 'research',
            title: 'Legal Research',
            description: 'Search Malaysian caselaw',
            icon: <BookOpen className="w-4 h-4" />,
            action: () => router.push('/research'),
            category: 'Navigation',
        },
        {
            id: 'evidence',
            title: 'Evidence & Hearing',
            description: 'Prepare court bundles',
            icon: <Scale className="w-4 h-4" />,
            action: () => router.push('/evidence'),
            category: 'Navigation',
        },
    ]

    const filteredCommands = commands.filter(cmd =>
        cmd.title.toLowerCase().includes(query.toLowerCase()) ||
        cmd.description?.toLowerCase().includes(query.toLowerCase())
    )

    // Focus input when opened
    useEffect(() => {
        if (isOpen) {
            setQuery('')
            setSelectedIndex(0)
            setTimeout(() => inputRef.current?.focus(), 100)
        }
    }, [isOpen])

    // Keyboard navigation
    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        if (!isOpen) return

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault()
                setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1))
                break
            case 'ArrowUp':
                e.preventDefault()
                setSelectedIndex(i => Math.max(i - 1, 0))
                break
            case 'Enter':
                e.preventDefault()
                if (filteredCommands[selectedIndex]) {
                    filteredCommands[selectedIndex].action()
                    onClose()
                }
                break
            case 'Escape':
                e.preventDefault()
                onClose()
                break
        }
    }, [isOpen, filteredCommands, selectedIndex, onClose])

    useEffect(() => {
        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [handleKeyDown])

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative min-h-full flex items-start justify-center pt-[15vh] px-4">
                <div className="glass-card w-full max-w-xl overflow-hidden animate-slide-up">
                    {/* Search input */}
                    <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200">
                        <Search className="w-5 h-5 text-gray-400" />
                        <input
                            ref={inputRef}
                            type="text"
                            placeholder="Search commands..."
                            value={query}
                            onChange={e => {
                                setQuery(e.target.value)
                                setSelectedIndex(0)
                            }}
                            className="flex-1 bg-transparent outline-none placeholder-gray-400"
                        />
                        <kbd className="hidden sm:inline-flex items-center px-2 py-1 text-xs font-mono bg-gray-100 text-gray-600 rounded">
                            ESC
                        </kbd>
                        <button
                            onClick={onClose}
                            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            <X className="w-4 h-4 text-gray-400" />
                        </button>
                    </div>

                    {/* Results */}
                    <div className="max-h-80 overflow-y-auto p-2">
                        {filteredCommands.length === 0 ? (
                            <div className="py-8 text-center text-gray-500">
                                No commands found
                            </div>
                        ) : (
                            <div className="space-y-1">
                                {filteredCommands.map((cmd, idx) => (
                                    <button
                                        key={cmd.id}
                                        onClick={() => {
                                            cmd.action()
                                            onClose()
                                        }}
                                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${idx === selectedIndex
                                                ? 'bg-blue-50 text-blue-900'
                                                : 'hover:bg-gray-50'
                                            }`}
                                    >
                                        <div className={`p-2 rounded-lg ${idx === selectedIndex
                                                ? 'bg-blue-100 text-blue-600'
                                                : 'bg-gray-100 text-gray-600'
                                            }`}>
                                            {cmd.icon}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium truncate">
                                                {cmd.title}
                                            </div>
                                            {cmd.description && (
                                                <div className="text-sm text-gray-500 truncate">
                                                    {cmd.description}
                                                </div>
                                            )}
                                        </div>
                                        {idx === selectedIndex && (
                                            <ArrowRight className="w-4 h-4 text-blue-600" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center gap-4 px-4 py-2 border-t border-gray-200 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">↑↓</kbd>
                            to navigate
                        </span>
                        <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">↵</kbd>
                            to select
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}

/**
 * Hook to manage command palette keyboard shortcut
 */
export function useCommandPalette() {
    const [isOpen, setIsOpen] = useState(false)

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault()
                setIsOpen(prev => !prev)
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [])

    return { isOpen, open: () => setIsOpen(true), close: () => setIsOpen(false) }
}
