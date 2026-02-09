'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
    User, Shield, Key, CheckCircle2, XCircle,
    AlertTriangle, Loader2, Cookie, Info, Globe,
    Trash2, Save, Eye, EyeOff
} from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'

export default function ProfilePage() {
    const [authMethod, setAuthMethod] = useState<'um_library' | 'cookies'>('um_library')
    const [cookieInput, setCookieInput] = useState('')
    const [showCookies, setShowCookies] = useState(false)
    const [validationStatus, setValidationStatus] = useState<{
        validated: boolean
        valid: boolean
        message: string
    } | null>(null)

    // Fetch current cookie status
    const { data: cookieStatus, refetch } = useQuery({
        queryKey: ['lexis-cookie-status'],
        queryFn: () => api.getLexisCookieStatus(),
    })

    // Validate cookies
    const validateMutation = useMutation({
        mutationFn: async (cookies: any[]) => {
            console.log('📡 API call starting with', cookies.length, 'cookies')
            const result = await api.validateLexisCookies(cookies)
            console.log('📥 API response:', result)
            return result
        },
        onSuccess: (data) => {
            console.log('✅ Validation success:', data)
            setValidationStatus({
                validated: true,
                valid: data.valid,
                message: data.message
            })
        },
        onError: (error: any) => {
            console.error('❌ Validation error:', error)
            setValidationStatus({
                validated: true,
                valid: false,
                message: error.response?.data?.detail || error.message || 'Validation failed'
            })
        }
    })

    // Save cookies
    const saveMutation = useMutation({
        mutationFn: async (cookies: any[]) => {
            return api.saveLexisCookies(cookies)
        },
        onSuccess: () => {
            refetch()
            setCookieInput('')
            setValidationStatus(null)
        }
    })

    // Clear cookies
    const clearMutation = useMutation({
        mutationFn: () => api.clearLexisCookies(),
        onSuccess: () => {
            refetch()
            setCookieInput('')
            setValidationStatus(null)
            setAuthMethod('um_library')
        }
    })

    const handleValidate = () => {
        try {
            // Trim whitespace and check if empty
            const trimmed = cookieInput.trim()
            if (!trimmed) {
                throw new Error('Please paste your cookies')
            }

            const cookies = JSON.parse(trimmed)
            if (!Array.isArray(cookies)) {
                throw new Error('Cookies must be an array')
            }

            if (cookies.length === 0) {
                throw new Error('Cookie array is empty')
            }

            validateMutation.mutate(cookies)
        } catch (error: any) {
            console.error('Cookie validation error:', error)
            setValidationStatus({
                validated: true,
                valid: false,
                message: error.message?.includes('JSON')
                    ? 'Invalid JSON format. Please paste cookies in JSON array format.'
                    : error.message || 'Invalid cookie format'
            })
        }
    }

    const handleSave = () => {
        try {
            const cookies = JSON.parse(cookieInput)
            saveMutation.mutate(cookies)
        } catch (error) {
            // Should not reach here if validation passed
        }
    }

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />
            <main className="flex-1 p-8">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="mb-8">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-12 h-12 rounded-lg bg-[var(--accent-gold)] flex items-center justify-center">
                                <User className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-4xl font-bold text-white">Profile Settings</h1>
                                <p className="text-[var(--text-secondary)] mt-1">
                                    Manage your account and preferences
                                </p>
                            </div>
                        </div>
                        <div className="cyber-line mt-6"></div>
                    </div>

                    {/* Lexis Authentication Settings */}
                    <div className="glass-card p-6 mb-6">
                        <div className="flex items-start justify-between mb-6">
                            <div>
                                <h2 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-[var(--accent-gold)]" />
                                    Lexis Authentication
                                </h2>
                                <p className="text-sm text-[var(--text-secondary)] mt-1">
                                    Configure how you authenticate to Lexis Advance
                                </p>
                            </div>

                            {cookieStatus?.has_cookies && (
                                <div className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 ${cookieStatus.is_expired
                                    ? 'bg-red-500/10 text-red-500'
                                    : 'bg-green-500/10 text-green-500'
                                    }`}>
                                    {cookieStatus.is_expired ? (
                                        <>
                                            <XCircle className="w-4 h-4" />
                                            Cookies Expired
                                        </>
                                    ) : (
                                        <>
                                            <CheckCircle2 className="w-4 h-4" />
                                            Active
                                        </>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Auth Method Selector */}
                        <div className="mb-6">
                            <label className="text-sm font-medium text-[var(--text-primary)] mb-3 block">
                                Authentication Method
                            </label>
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    onClick={() => setAuthMethod('um_library')}
                                    className={`p-4 rounded-xl border-2 transition-all ${authMethod === 'um_library'
                                        ? 'border-[var(--accent-gold)] bg-[var(--accent-gold)]/5'
                                        : 'border-[var(--border)] hover:border-[var(--border-secondary)]'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <Globe className={`w-5 h-5 ${authMethod === 'um_library'
                                            ? 'text-[var(--accent-gold)]'
                                            : 'text-[var(--text-tertiary)]'
                                            }`} />
                                        <div className="text-left">
                                            <div className="font-semibold text-[var(--text-primary)]">
                                                UM Library
                                            </div>
                                            <div className="text-xs text-[var(--text-tertiary)]">
                                                Default (15-20s)
                                            </div>
                                        </div>
                                    </div>
                                </button>

                                <button
                                    onClick={() => setAuthMethod('cookies')}
                                    className={`p-4 rounded-xl border-2 transition-all ${authMethod === 'cookies'
                                        ? 'border-[#22c55e] bg-[#22c55e]/5'
                                        : 'border-[var(--border)] hover:border-[var(--border-secondary)]'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <Cookie className={`w-5 h-5 ${authMethod === 'cookies'
                                            ? 'text-[#22c55e]'
                                            : 'text-[var(--text-tertiary)]'
                                            }`} />
                                        <div className="text-left">
                                            <div className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
                                                My Cookies
                                                <span className="text-[10px] px-1.5 py-0.5 bg-[#22c55e]/20 text-[#22c55e] rounded">
                                                    FAST
                                                </span>
                                            </div>
                                            <div className="text-xs text-[var(--text-tertiary)]">
                                                Advanced (5-8s)
                                            </div>
                                        </div>
                                    </div>
                                </button>
                            </div>
                        </div>

                        {/* Cookie Configuration (shown when "My Cookies" selected) */}
                        {authMethod === 'cookies' && (
                            <div className="space-y-4 animate-slide-up">
                                {/* Info Banner */}
                                <div className="p-4 rounded-xl bg-[#D4A853]/10 border border-[#D4A853]/20">
                                    <div className="flex gap-3">
                                        <Info className="w-5 h-5 text-[#D4A853] flex-shrink-0 mt-0.5" />
                                        <div className="text-sm text-[var(--text-secondary)]">
                                            <p className="font-medium text-[var(--text-primary)] mb-1">
                                                How to get your Lexis cookies:
                                            </p>
                                            <ol className="list-decimal list-inside space-y-1 text-xs">
                                                <li>Log in to Lexis Advance in your browser</li>
                                                <li>Install <a href="https://chrome.google.com/webstore/detail/editthiscookie/" target="_blank" rel="noopener noreferrer" className="text-[#D4A853] hover:underline">EditThisCookie</a> extension</li>
                                                <li>Click the extension → Export (JSON format)</li>
                                                <li>Paste the JSON below</li>
                                            </ol>
                                        </div>
                                    </div>
                                </div>

                                {/* Cookie Input */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-sm font-medium text-[var(--text-primary)]">
                                            Cookie Data (JSON)
                                        </label>
                                        <button
                                            onClick={() => setShowCookies(!showCookies)}
                                            className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] flex items-center gap-1"
                                        >
                                            {showCookies ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                                            {showCookies ? 'Hide' : 'Show'}
                                        </button>
                                    </div>
                                    <textarea
                                        value={cookieInput}
                                        onChange={(e) => {
                                            setCookieInput(e.target.value)
                                            setValidationStatus(null)
                                        }}
                                        placeholder='[{"name": "LexisAdvance_SessionId", "value": "...", "domain": ".advance.lexis.com"}]'
                                        rows={showCookies ? 8 : 3}
                                        className={`w-full px-4 py-3 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-[var(--accent-gold)] focus:ring-1 focus:ring-[var(--accent-gold)] transition-all font-mono text-xs ${!showCookies ? 'text-security-disc' : ''
                                            }`}
                                    />
                                </div>

                                {/* Validation Status */}
                                {validationStatus && (
                                    <div className={`p-4 rounded-xl flex items-start gap-3 ${validationStatus.valid
                                        ? 'bg-green-500/10 border border-green-500/20'
                                        : 'bg-red-500/10 border border-red-500/20'
                                        }`}>
                                        {validationStatus.valid ? (
                                            <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                                        )}
                                        <div>
                                            <p className={`font-medium ${validationStatus.valid ? 'text-green-500' : 'text-red-500'
                                                }`}>
                                                {validationStatus.valid ? 'Cookies Valid' : 'Validation Failed'}
                                            </p>
                                            <p className="text-sm text-[var(--text-secondary)] mt-1">
                                                {validationStatus.message}
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* Action Buttons */}
                                <div className="flex gap-3">
                                    <button
                                        onClick={handleValidate}
                                        disabled={!cookieInput.trim() || validateMutation.isPending}
                                        className="flex-1 px-4 py-3 rounded-xl bg-[var(--accent-gold)]/10 text-[var(--accent-gold)] font-medium hover:bg-[var(--accent-gold)]/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                                    >
                                        {validateMutation.isPending ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                Validating (15-30s)...
                                            </>
                                        ) : (
                                            <>
                                                <Key className="w-4 h-4" />
                                                Validate
                                            </>
                                        )}
                                    </button>

                                    <button
                                        onClick={handleSave}
                                        disabled={!validationStatus?.valid || saveMutation.isPending}
                                        className="flex-1 px-4 py-3 rounded-xl bg-[#22c55e] text-white font-medium hover:bg-[#22c55e]/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                                    >
                                        {saveMutation.isPending ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                Saving...
                                            </>
                                        ) : (
                                            <>
                                                <Save className="w-4 h-4" />
                                                Save
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Current Status (when cookies are saved) */}
                        {cookieStatus?.has_cookies && (
                            <div className="mt-6 p-4 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border)]">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="font-medium text-[var(--text-primary)] mb-1">
                                            Current Configuration
                                        </p>
                                        <p className="text-sm text-[var(--text-secondary)]">
                                            Using saved cookies • Expires: {new Date(cookieStatus.expires_at).toLocaleString()}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => clearMutation.mutate()}
                                        disabled={clearMutation.isPending}
                                        className="px-4 py-2 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-all flex items-center gap-2 text-sm font-medium"
                                    >
                                        {clearMutation.isPending ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <>
                                                <Trash2 className="w-4 h-4" />
                                                Clear Cookies
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Privacy Notice */}
                    <div className="glass-card p-4 bg-[var(--accent-gold)]/5 border border-[var(--accent-gold)]/20">
                        <div className="flex gap-3">
                            <Shield className="w-5 h-5 text-[var(--accent-gold)] flex-shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <p className="font-medium text-[var(--text-primary)] mb-1">
                                    Privacy & Security
                                </p>
                                <p className="text-[var(--text-secondary)] text-xs">
                                    Your cookies are encrypted using AES-256 and stored securely in our database.
                                    They are never exposed in frontend code, logs, or network requests.
                                    You can revoke access at any time by clicking "Clear Cookies" above.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}
