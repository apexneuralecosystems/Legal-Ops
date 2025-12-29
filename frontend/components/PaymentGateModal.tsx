'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSubscriptionStore } from '@/lib/subscriptionStore'

interface PaymentRequiredDetail {
    message: string
    redirectUrl: string
    workflowType: string
}

export default function PaymentGateModal() {
    const router = useRouter()
    const {
        showPaymentModal,
        paymentMessage,
        paymentWorkflow,
        closePaymentModal
    } = useSubscriptionStore()

    // Listen for 402 events from API
    useEffect(() => {
        const handlePaymentRequired = (event: CustomEvent<PaymentRequiredDetail>) => {
            const { message, workflowType } = event.detail
            useSubscriptionStore.getState().openPaymentModal(message, workflowType)
        }

        window.addEventListener('paymentRequired', handlePaymentRequired as EventListener)

        return () => {
            window.removeEventListener('paymentRequired', handlePaymentRequired as EventListener)
        }
    }, [])

    const handleSubscribe = () => {
        closePaymentModal()
        router.push('/pricing')
    }

    if (!showPaymentModal) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={closePaymentModal}
            />

            {/* Modal */}
            <div className="relative glass-card p-8 max-w-md w-full mx-4 shadow-2xl shadow-[var(--gold-primary)]/10">
                {/* Icon */}
                <div className="flex justify-center mb-6">
                    <div className="w-16 h-16 rounded-full bg-[var(--gradient-gold)] flex items-center justify-center shadow-lg shadow-[var(--gold-primary)]/20">
                        <svg className="w-8 h-8 text-[#0d1117]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>
                </div>

                {/* Title */}
                <h2 className="text-2xl font-bold text-center text-white mb-2">
                    Free Trial Limit Reached
                </h2>

                {/* Message */}
                <p className="text-gray-300 text-center mb-6">
                    {paymentMessage || `You've used your free ${paymentWorkflow} trial. Subscribe to unlock unlimited access to all workflows.`}
                </p>

                {/* Workflow Badge */}
                {paymentWorkflow && (
                    <div className="flex justify-center mb-6">
                        <span className="px-4 py-1 bg-[var(--gold-primary)]/10 text-[var(--gold-primary)] rounded-full text-sm capitalize border border-[var(--gold-primary)]/20">
                            {paymentWorkflow} Workflow
                        </span>
                    </div>
                )}

                {/* Benefits */}
                <div className="bg-slate-700/50 rounded-xl p-4 mb-6">
                    <p className="text-sm text-gray-400 mb-3">Subscribe to get:</p>
                    <ul className="space-y-2">
                        <li className="flex items-center text-white text-sm">
                            <svg className="w-4 h-4 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            Unlimited workflow runs
                        </li>
                        <li className="flex items-center text-white text-sm">
                            <svg className="w-4 h-4 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            Priority support
                        </li>
                        <li className="flex items-center text-white text-sm">
                            <svg className="w-4 h-4 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            All future features
                        </li>
                    </ul>
                </div>

                {/* Buttons */}
                <div className="flex gap-3">
                    <button
                        onClick={closePaymentModal}
                        className="flex-1 py-3 px-4 rounded-xl border border-gray-600 text-gray-300 hover:bg-slate-700 transition-colors"
                    >
                        Maybe Later
                    </button>
                    <button
                        onClick={handleSubscribe}
                        className="flex-1 btn-primary text-[#0d1117] hover:scale-105"
                    >
                        Subscribe Now
                    </button>
                </div>
            </div>
        </div>
    )
}
