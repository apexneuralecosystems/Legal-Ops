'use client'

import { useEffect, useState } from 'react'
import { FolderOpen, Sparkles } from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import MatterSummaryPanel from '@/components/MatterSummaryPanel'

import { api } from '@/lib/api'

export default function MattersPage() {
    const [matters, setMatters] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchMatters()

        const interval = setInterval(fetchMatters, 10000)
        return () => clearInterval(interval)
    }, [])

    const fetchMatters = async () => {
        try {
            const data = await api.getMatters()
            setMatters(data)
        } catch (error) {
            console.error('Failed to fetch matters:', error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />

            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-purple)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--neon-cyan)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                <div className="mb-10 animate-fade-in">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="icon-box w-12 h-12">
                            <FolderOpen className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold gradient-text">All Matters</h1>
                            <p className="text-[var(--text-secondary)] mt-1">
                                Comprehensive list of all legal matters in the system
                            </p>
                        </div>
                    </div>
                    <div className="cyber-line mt-6"></div>
                </div>

                {loading ? (
                    <div className="card p-12 text-center animate-slide-up">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-cyan)] flex items-center justify-center shadow-lg animate-pulse">
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <p className="text-[var(--text-secondary)]">Loading matters...</p>
                    </div>
                ) : (
                    <div className="animate-slide-up">
                        <MatterSummaryPanel matters={matters} />
                    </div>
                )}
            </main>
        </div>
    )
}
