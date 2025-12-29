'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/authStore'
import { useSubscriptionStore } from '@/lib/subscriptionStore'
import { paymentsApi, subscriptionApi } from '@/lib/api'

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
            <div className="container mx-auto px-4 py-16">
                {/* Header */}
                <div className="text-center mb-16">
                    <h1 className="text-5xl font-bold text-[var(--text-primary)] mb-4">
                        Unlock <span className="gradient-text">Unlimited</span> Access
                    </h1>
                    <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                        Get unlimited access to all Legal-Ops AI workflows and supercharge your legal practice
                    </p>
                </div>

                {/* Pricing Cards */}
                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    {/* Free Tier */}
                    <div className="card p-8">
                        <div className="mb-6">
                            <h3 className="text-2xl font-semibold text-white">Free Trial</h3>
                            <p className="text-gray-400 mt-2">Get started with limited access</p>
                        </div>

                        <div className="mb-6">
                            <span className="text-4xl font-bold text-white">$0</span>
                            <span className="text-gray-400">/forever</span>
                        </div>

                        <ul className="space-y-3 mb-8">
                            <li className="flex items-center text-gray-300">
                                <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                1 free Intake workflow
                            </li>
                            <li className="flex items-center text-gray-300">
                                <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                1 free Drafting workflow
                            </li>
                            <li className="flex items-center text-gray-300">
                                <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                1 free Evidence workflow
                            </li>
                            <li className="flex items-center text-gray-300">
                                <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                1 free Research workflow
                            </li>
                        </ul>

                        <button
                            disabled
                            className="w-full py-3 px-6 rounded-xl bg-slate-700 text-gray-400 cursor-not-allowed"
                        >
                            Current Plan
                        </button>
                    </div>

                    {/* Pro Tier */}
                    <div className="glass-card p-8 relative overflow-hidden ring-1 ring-[var(--gold-primary)]">
                        <div className="absolute top-0 right-0 bg-[var(--gradient-gold)] text-[#0d1117] text-sm font-bold px-4 py-1 rounded-bl-xl">
                            RECOMMENDED
                        </div>

                        <div className="mb-6">
                            <h3 className="text-2xl font-semibold text-white">Pro</h3>
                            <p className="text-gray-300 mt-2">Unlimited access to all features</p>
                        </div>

                        <div className="mb-6">
                            <span className="text-4xl font-bold text-[var(--gold-primary)]">$29.99</span>
                            <span className="text-gray-300">/month</span>
                        </div>

                        <ul className="space-y-3 mb-8">
                            <li className="flex items-center text-white">
                                <svg className="w-5 h-5 text-[var(--gold-primary)] mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                <strong>Unlimited</strong>&nbsp;Intake workflows
                            </li>
                            <li className="flex items-center text-white">
                                <svg className="w-5 h-5 text-[var(--gold-primary)] mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                <strong>Unlimited</strong>&nbsp;Drafting workflows
                            </li>
                            <li className="flex items-center text-white">
                                <svg className="w-5 h-5 text-[var(--gold-primary)] mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                <strong>Unlimited</strong>&nbsp;Evidence workflows
                            </li>
                            <li className="flex items-center text-white">
                                <svg className="w-5 h-5 text-[var(--gold-primary)] mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                <strong>Unlimited</strong>&nbsp;Research workflows
                            </li>
                            <li className="flex items-center text-white">
                                <svg className="w-5 h-5 text-[var(--gold-primary)] mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
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
                            className={`w-full py-3 px-6 rounded-xl font-semibold transition-all duration-300 ${isPro
                                ? 'bg-green-600 text-white cursor-not-allowed'
                                : isProcessing
                                    ? 'bg-[var(--gold-primary)]/50 text-white cursor-wait'
                                    : 'btn-primary text-[#0d1117] hover:scale-105'
                                }`}
                        >
                            {isPro ? '✓ Already Subscribed' : isProcessing ? 'Processing...' : 'Subscribe Now'}
                        </button>
                    </div>
                </div>

                {/* Usage Status (if authenticated) */}
                {isAuthenticated && usageStatus && (
                    <div className="mt-16 max-w-4xl mx-auto">
                        <h2 className="text-2xl font-semibold text-white mb-6 text-center">Your Current Usage</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(usageStatus.usage).map(([workflow, data]) => (
                                <div key={workflow} className="bg-slate-800/50 rounded-xl p-4 text-center">
                                    <div className="text-gray-400 capitalize mb-2">{workflow}</div>
                                    <div className="text-2xl font-bold text-white">
                                        {data.used} / {data.limit === 'unlimited' ? '∞' : data.limit}
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        {data.remaining === 'unlimited' ? 'Unlimited' : `${data.remaining} remaining`}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Back to Dashboard */}
                <div className="mt-12 text-center">
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        ← Back to Dashboard
                    </button>
                </div>
            </div>
        </div>
    )
}
