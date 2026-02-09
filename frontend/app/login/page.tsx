'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Scale, Mail, Lock, Loader2, ArrowRight } from 'lucide-react'
import { useAuthStore } from '@/lib/authStore'
import Image from 'next/image'

export default function LoginPage() {
    const router = useRouter()
    const { login } = useAuthStore()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            await login({ email, password })
            router.push('/dashboard')
        } catch (err: any) {
            setError(err.message || 'Invalid credentials')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-slate-200 font-sans selection:bg-[#D4A853] selection:text-white flex items-center justify-center relative overflow-hidden">

            {/* Cinematic Background */}
            <div className="absolute inset-0 z-0">
                <img
                    src="/hero-scales.jpg"
                    alt="Background"
                    className="absolute inset-0 w-full h-full object-cover opacity-20 scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-primary)] via-[var(--bg-primary)]/60 to-[var(--bg-primary)]/80"></div>
                <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"></div>
            </div>

            {/* Back Navigation */}
            <Link href="/" className="absolute top-8 left-8 z-20 flex items-center gap-2 text-slate-400 hover:text-[#D4A853] transition-colors group">
                <div className="p-2 rounded-full border border-[var(--border)] group-hover:border-[#D4A853] transition-all">
                    <ArrowRight className="w-4 h-4 rotate-180" />
                </div>
                <span className="text-xs font-bold tracking-widest uppercase opacity-0 group-hover:opacity-100 transition-all -ml-2 group-hover:ml-0">Back to Home</span>
            </Link>

            {/* Glass Card */}
            <div className="relative z-10 w-full max-w-md p-8 md:p-12">
                {/* Branding */}
                <div className="flex flex-col items-center mb-10">
                    <div className="w-12 h-12 bg-[#D4A853] rounded-full flex items-center justify-center text-black mb-4 shadow-[0_0_20px_rgba(212,168,83,0.3)]">
                        <Scale className="w-6 h-6" />
                    </div>
                    <h1 className="text-3xl font-serif font-bold text-center mb-2 tracking-tight">Welcome Back</h1>
                    <p className="text-slate-300 text-sm text-center uppercase tracking-widest">Legal Intelligence Portal</p>
                </div>

                {/* Glass Container */}
                <div className="bg-[#D4A853]/5 backdrop-blur-xl border border-[var(--border)] rounded-2xl p-8 shadow-2xl">
                    {error && (
                        <div className="mb-6 p-4 bg-red-500/10 text-red-400 rounded-lg text-sm border border-red-500/20 flex items-center gap-2">
                            <div className="w-1 h-4 bg-red-500 rounded-full"></div>
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-[#D4A853] uppercase tracking-widest">Email</label>
                            <div className="relative group">
                                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-[#D4A853] transition-colors" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-black/60 border border-[#D4A853]/20 rounded-lg focus:outline-none focus:border-[#D4A853] focus:ring-1 focus:ring-[#D4A853] text-slate-200 placeholder-gray-500 transition-all font-light"
                                    placeholder="lawyer@firm.com"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-bold text-[#D4A853] uppercase tracking-widest">Password</label>
                                <Link
                                    href="/forgot-password"
                                    className="text-[10px] items-center text-slate-400 hover:text-[#D4A853] transition-colors uppercase tracking-wider"
                                >
                                    Forgot password?
                                </Link>
                            </div>
                            <div className="relative group">
                                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-[#D4A853] transition-colors" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-black/60 border border-[#D4A853]/20 rounded-lg focus:outline-none focus:border-[#D4A853] focus:ring-1 focus:ring-[#D4A853] text-slate-200 placeholder-gray-500 transition-all font-light"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[#D4A853] hover:bg-[#E8C775] text-black font-bold py-4 rounded-lg flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_rgba(212,168,83,0.1)] hover:shadow-[0_0_30px_rgba(212,168,83,0.3)] disabled:opacity-70 disabled:cursor-not-allowed uppercase tracking-widest text-xs"
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    Sign In <ArrowRight className="w-4 h-4" />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                <p className="mt-8 text-center text-xs text-slate-400 tracking-wide">
                    Don't have an account?{' '}
                    <Link href="/signup" className="font-bold text-[#D4A853] hover:text-[#E8C775] transition-colors underline decoration-[#D4A853]/50 underline-offset-4">
                        Request Access
                    </Link>
                </p>

                <div className="mt-12 text-center text-[10px] text-gray-600 uppercase tracking-[0.2em]">
                    Secured by ApexNeural
                </div>
            </div>
        </div>
    )
}
