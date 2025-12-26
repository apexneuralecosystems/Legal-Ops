'use client'

import { create } from 'zustand'
import { subscriptionApi, UsageStatus, WorkflowAccess } from './api'

interface SubscriptionState {
    usageStatus: UsageStatus | null
    isLoading: boolean
    error: string | null
    showPaymentModal: boolean
    paymentMessage: string
    paymentWorkflow: string

    // Actions
    fetchUsageStatus: () => Promise<void>
    checkWorkflowAccess: (workflowType: string) => Promise<WorkflowAccess | null>
    activateSubscription: (subscriptionId: string) => Promise<boolean>
    cancelSubscription: () => Promise<boolean>
    openPaymentModal: (message: string, workflow: string) => void
    closePaymentModal: () => void
    clearError: () => void
}

export const useSubscriptionStore = create<SubscriptionState>()((set, get) => ({
    usageStatus: null,
    isLoading: false,
    error: null,
    showPaymentModal: false,
    paymentMessage: '',
    paymentWorkflow: '',

    fetchUsageStatus: async () => {
        set({ isLoading: true, error: null })
        try {
            const status = await subscriptionApi.getUsageStatus()
            set({ usageStatus: status, isLoading: false })
        } catch (error: any) {
            set({
                isLoading: false,
                error: error.message || 'Failed to fetch usage status'
            })
        }
    },

    checkWorkflowAccess: async (workflowType: string) => {
        try {
            const access = await subscriptionApi.checkWorkflowAccess(workflowType)
            if (!access.can_access) {
                set({
                    showPaymentModal: true,
                    paymentMessage: `You've used your free ${workflowType} trial. Subscribe to continue!`,
                    paymentWorkflow: workflowType
                })
            }
            return access
        } catch (error: any) {
            console.error('Error checking workflow access:', error)
            return null
        }
    },

    activateSubscription: async (subscriptionId: string) => {
        set({ isLoading: true, error: null })
        try {
            await subscriptionApi.activateSubscription(subscriptionId)
            // Refresh usage status
            await get().fetchUsageStatus()
            set({ isLoading: false, showPaymentModal: false })
            return true
        } catch (error: any) {
            set({
                isLoading: false,
                error: error.message || 'Failed to activate subscription'
            })
            return false
        }
    },

    cancelSubscription: async () => {
        set({ isLoading: true, error: null })
        try {
            await subscriptionApi.cancelSubscription()
            await get().fetchUsageStatus()
            set({ isLoading: false })
            return true
        } catch (error: any) {
            set({
                isLoading: false,
                error: error.message || 'Failed to cancel subscription'
            })
            return false
        }
    },

    openPaymentModal: (message: string, workflow: string) => {
        set({
            showPaymentModal: true,
            paymentMessage: message,
            paymentWorkflow: workflow
        })
    },

    closePaymentModal: () => {
        set({ showPaymentModal: false, paymentMessage: '', paymentWorkflow: '' })
    },

    clearError: () => {
        set({ error: null })
    }
}))

export default useSubscriptionStore
