'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/lib/authStore'
import { useSubscriptionStore } from '@/lib/subscriptionStore'
import { paymentsApi, subscriptionApi } from '@/lib/api'
import { Scale, ArrowLeft, Check, Sparkles } from 'lucide-react'

export default function PricingPage() {
    const router = useRouter()
    const { isAuthenticated } = useAuthStore()
    const { usageStatus, fetchUsageStatus, isLoading } = useSubscriptionStore()
    const [isProcessing, setIsProcessing] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (isAuthenticated) {
            fetchUsageStatus()
        }
    }, [isAuthenticated, fetchUsageStatus])

    const handleSubscribe = async () => {
        if (!isAuthenticated) {
            router.push('/login?redirect=/pricing')
            return
        }

        setIsProcessing(true)
        setError(null)

        try {
            // Create PayPal order
            const order = await paymentsApi.createOrder(29.99, 'USD', 'Legal-Ops Pro Subscription')

            if (order.approval_url) {
                // Redirect to PayPal for payment
                window.location.href = order.approval_url
            } else {
                // For sandbox/demo, simulate instant activation
                await subscriptionApi.activateSubscription(order.order_id)
                await fetchUsageStatus()
                router.push('/dashboard?subscribed=true')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to process subscription')
        } finally {
            setIsProcessing(false)
        }
    }

    const isPro = usageStatus?.has_paid && usageStatus?.subscription_status === 'active'

    return (
        <div className="min-h-screen bg-[var(--bg-primary)]">
            {/* Header */}
            <header className="px-10 py-8 border-b border-[var(--border)] flex items-center justify-between sticky top-0 bg-[var(--bg-primary)]/90 backdrop-blur z-50">
                <div className="flex items-center gap-4">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[var(--bg-secondary)] rounded-lg flex items-center justify-center">
                            <Scale className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">LEGALOPS</span>
                    </Link>
                </div>
            </header>

            <div className="container mx-auto px-4 py-16">
                {/* Header */}
                <div className="text-center mb-16">
                    <h1 className="text-5xl font-black text-white mb-4">
                        Unlock <span className="text-[#D4A853]">Unlimited</span> Access
                    </h1>
                    <p className="text-xl text-slate-400 max-w-2xl mx-auto">
                        Get unlimited access to all Legal-Ops AI workflows and supercharge your legal practice
                    </p>
                </div>

                {/* Pricing Cards */}
                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    {/* Free Tier */}
                    <div className="bg-[var(--bg-secondary)] border-2 border-[#D4A853]/20 rounded-2xl p-8">
                        <div className="mb-6">
                            <h3 className="text-2xl font-bold text-white">Free Trial</h3>
                            <p className="text-gray-500 mt-2">Get started with limited access</p>
                        </div>

                        <div className="mb-6">
                            <span className="text-4xl font-black text-white">$0</span>
                            <span className="text-gray-500">/forever</span>
                        </div>

                        <ul className="space-y-3 mb-8">
                            <li className="flex items-center text-slate-300">
                                <Check className="w-5 h-5 text-green-600 mr-3" />
                                1 free Intake workflow
                            </li>
                            <li className="flex items-center text-slate-300">
                                <Check className="w-5 h-5 text-green-600 mr-3" />
                                1 free Drafting workflow
                            </li>
                            <li className="flex items-center text-slate-300">
                                <Check className="w-5 h-5 text-green-600 mr-3" />
                                1 free Evidence workflow
                            </li>
                            <li className="flex items-center text-slate-300">
                                <Check className="w-5 h-5 text-green-600 mr-3" />
                                1 free Research workflow
                            </li>
                        </ul>

                        <button
                            disabled
                            className="w-full py-3 px-6 rounded-xl bg-[var(--bg-tertiary)] text-gray-400 cursor-not-allowed border border-[#D4A853]/20"
                        >
                            Current Plan
                        </button>
                    </div>

                    {/* Pro Tier */}
                    <div className="bg-black text-white rounded-2xl p-8 relative overflow-hidden">
                        <div className="absolute top-0 right-0 bg-[#D4A853] text-white text-sm font-bold px-4 py-1 rounded-bl-xl flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            RECOMMENDED
                        </div>

                        <div className="mb-6">
                            <h3 className="text-2xl font-bold">Pro</h3>
                            <p className="text-gray-400 mt-2">Unlimited access to all features</p>
                        </div>

                        <div className="mb-6">
                            <span className="text-4xl font-black text-[#D4A853]">$29.99</span>
                            <span className="text-gray-400">/month</span>
                        </div>

                        <ul className="space-y-3 mb-8">
                            <li className="flex items-center">
                                <Check className="w-5 h-5 text-[#D4A853] mr-3" />
                                <strong>Unlimited</strong>&nbsp;Intake workflows
                            </li>
                            <li className="flex items-center">
                                <Check className="w-5 h-5 text-[#D4A853] mr-3" />
                                <strong>Unlimited</strong>&nbsp;Drafting workflows
                            </li>
                            <li className="flex items-center">
                                <Check className="w-5 h-5 text-[#D4A853] mr-3" />
                                <strong>Unlimited</strong>&nbsp;Evidence workflows
                            </li>
                            <li className="flex items-center">
                                <Check className="w-5 h-5 text-[#D4A853] mr-3" />
                                <strong>Unlimited</strong>&nbsp;Research workflows
                            </li>
                            <li className="flex items-center">
                                <Check className="w-5 h-5 text-[#D4A853] mr-3" />
                                Priority support
                            </li>
                        </ul>

                        {error && (
                            <div className="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-300 text-sm">
                                {error}
                            </div>
                        )}

                        <button
                            onClick={handleSubscribe}
                            disabled={isProcessing || isPro}
                            className={`w-full py-3 px-6 rounded-xl font-bold transition-all duration-300 ${isPro
                                ? 'bg-green-600 text-white cursor-not-allowed'
                                : isProcessing
                                    ? 'bg-gray-600 text-white cursor-wait'
                                    : 'bg-[var(--bg-secondary)] text-white hover:bg-[var(--bg-tertiary)]'
                                }`}
                        >
                            {isPro ? '✓ Already Subscribed' : isProcessing ? 'Processing...' : 'Subscribe Now'}
                        </button>
                    </div>
                </div>

                {/* Usage Status (if authenticated) */}
                {isAuthenticated && usageStatus && (
                    <div className="mt-16 max-w-4xl mx-auto">
                        <h2 className="text-2xl font-bold text-white mb-6 text-center">Your Current Usage</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(usageStatus.usage).map(([workflow, data]) => (
                                <div key={workflow} className="bg-slate-950 border border-[#D4A853]/20 rounded-xl p-4 text-center">
                                    <div className="text-gray-500 capitalize mb-2">{workflow}</div>
                                    <div className="text-2xl font-bold text-white">
                                        {data.used} / {data.limit === 'unlimited' ? '∞' : data.limit}
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        {data.remaining === 'unlimited' ? 'Unlimited' : `${data.remaining} remaining`}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Footer */}
            <footer className="bg-black text-white py-8 px-6 mt-16">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-[var(--bg-secondary)] rounded flex items-center justify-center">
                            <Scale className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-lg font-bold">LEGALOPS</span>
                    </div>
                    <span className="text-gray-500 text-sm">© 2026 LegalOps AI. All rights reserved.</span>
                </div>
            </footer>
        </div >
    )
}
