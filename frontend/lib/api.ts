import axios, { AxiosInstance, AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios'

// API Configuration
// For authenticated requests, we need to call the backend directly from the browser
// so that Authorization headers from localStorage can be included.
// CORS is handled by the backend's CORSMiddleware.

// PUBLIC URL: Used by the browser (client-side)
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8091'

// INTERNAL URL: Used by Next.js server (SSR) to talk to backend container
// If INTERNAL_API_URL is not set, fall back to PUBLIC_API_URL
const INTERNAL_API_URL = process.env.INTERNAL_API_URL || PUBLIC_API_URL

// Determine which URL to use based on environment (Server vs Client)
const API_URL = typeof window === 'undefined' ? INTERNAL_API_URL : PUBLIC_API_URL

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

// Types
export interface AuthTokens {
    access_token: string
    refresh_token: string
    token_type: string
}

export interface UserInfo {
    id: string
    email: string
    full_name?: string
    username?: string
    is_active: boolean
}

export interface SignupData {
    email: string
    password: string
    full_name?: string
    username?: string
}

export interface LoginData {
    email: string
    password: string
}

export interface ApiError {
    status: 'error'
    message: string
    detail?: string
    statusCode: number
}

// Token management helpers
export const tokenManager = {
    getAccessToken: (): string | null => {
        if (typeof window === 'undefined') return null
        return localStorage.getItem(ACCESS_TOKEN_KEY)
    },

    getRefreshToken: (): string | null => {
        if (typeof window === 'undefined') return null
        return localStorage.getItem(REFRESH_TOKEN_KEY)
    },

    setTokens: (tokens: AuthTokens): void => {
        if (typeof window === 'undefined') return
        localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
    },

    clearTokens: (): void => {
        if (typeof window === 'undefined') return
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
    },

    isAuthenticated: (): boolean => {
        return !!tokenManager.getAccessToken()
    }
}

// Create axios instance with interceptors
const createApiClient = (): AxiosInstance => {
    const client = axios.create({
        baseURL: `${API_URL}/api`,
        timeout: 300000, // 5 minutes (Lexis scraper can take ~90s)
        headers: {
            'Content-Type': 'application/json',
        },
    })

    // Request interceptor - Add auth token
    client.interceptors.request.use(
        (config: InternalAxiosRequestConfig) => {
            const token = tokenManager.getAccessToken()
            if (token && config.headers) {
                config.headers.Authorization = `Bearer ${token}`
            }
            return config
        },
        (error: AxiosError) => {
            return Promise.reject(error)
        }
    )

    // Response interceptor - Handle errors and token refresh
    client.interceptors.response.use(
        (response: AxiosResponse) => response,
        async (error: AxiosError) => {
            const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

            // Handle 401 - Try to refresh token
            if (error.response?.status === 401 && !originalRequest._retry) {
                originalRequest._retry = true

                try {
                    const refreshToken = tokenManager.getRefreshToken()
                    if (refreshToken) {
                        const response = await axios.post(`${API_URL}/api/auth/refresh`, {
                            refresh_token: refreshToken
                        })

                        if (response.data.access_token) {
                            tokenManager.setTokens(response.data)

                            if (originalRequest.headers) {
                                originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`
                            }

                            return client(originalRequest)
                        }
                    }
                } catch (refreshError) {
                    tokenManager.clearTokens()
                    if (typeof window !== 'undefined') {
                        window.location.href = '/login'
                    }
                }
            }

            // Handle 402 - Payment Required (Freemium limit reached)
            if (error.response?.status === 402) {
                const detail = (error.response?.data as any)?.detail || {}
                const paymentRequiredEvent = new CustomEvent('paymentRequired', {
                    detail: {
                        message: detail.message || 'Free usage limit reached. Please subscribe to continue.',
                        redirectUrl: detail.redirect_url || '/pricing',
                        workflowType: detail.workflow_type || 'unknown'
                    }
                })
                if (typeof window !== 'undefined') {
                    window.dispatchEvent(paymentRequiredEvent)
                }
            }

            // Format error for consistent handling
            const apiError: ApiError = {
                status: 'error',
                message: extractErrorMessage(error),
                detail: (error.response?.data as Record<string, unknown>)?.detail as string,
                statusCode: error.response?.status || 500
            }

            return Promise.reject(apiError)
        }
    )

    return client
}

// Extract user-friendly error message
const extractErrorMessage = (error: AxiosError): string => {
    if (error.response?.data) {
        const data = error.response.data as any
        if (data.detail) {
            if (typeof data.detail === 'string') return data.detail
            if (Array.isArray(data.detail)) return data.detail.map((e: any) => e.msg).join(', ')
            return JSON.stringify(data.detail)
        }
        if (data.message) return data.message
    }

    if (error.message === 'Network Error') {
        return 'Unable to connect to server. Please check your connection.'
    }

    if (error.code === 'ECONNABORTED') {
        return 'Request timed out. Please try again.'
    }

    return 'An unexpected error occurred. Please try again.'
}

const apiClient = createApiClient()

// Auth API
export const authApi = {
    signup: async (data: SignupData): Promise<UserInfo> => {
        try {
            const response = await apiClient.post('/auth/signup', data)
            return response.data
        } catch (error) {
            throw error
        }
    },

    login: async (data: LoginData): Promise<AuthTokens> => {
        try {
            const response = await apiClient.post('/auth/login', data)
            const tokens = response.data
            tokenManager.setTokens(tokens)
            return tokens
        } catch (error) {
            throw error
        }
    },

    logout: (): void => {
        tokenManager.clearTokens()
    },

    verifyToken: async (token: string): Promise<boolean> => {
        try {
            await apiClient.post('/auth/verify', null, {
                params: { token }
            })
            return true
        } catch (error) {
            return false
        }
    },

    refreshToken: async (): Promise<AuthTokens | null> => {
        try {
            const refreshToken = tokenManager.getRefreshToken()
            if (!refreshToken) return null

            const response = await apiClient.post('/auth/refresh', {
                refresh_token: refreshToken
            })
            tokenManager.setTokens(response.data)
            return response.data
        } catch (error) {
            tokenManager.clearTokens()
            return null
        }
    },

    forgotPassword: async (email: string): Promise<{ message: string }> => {
        try {
            const response = await apiClient.post('/auth/forgot-password', { email })
            return response.data
        } catch (error) {
            throw error
        }
    },

    resetPassword: async (token: string, newPassword: string): Promise<{ message: string }> => {
        try {
            const response = await apiClient.post('/auth/reset-password', {
                token,
                new_password: newPassword
            })
            return response.data
        } catch (error) {
            throw error
        }
    }
}

// Main API with try/catch handling
export const api = {
    // Matters
    getMatters: async (status?: string | null) => {
        try {
            const params = status ? { status } : {}
            const response = await apiClient.get('/matters/', { params })
            return response.data
        } catch (error) {
            console.error('Error fetching matters:', error)
            throw error
        }
    },

    getMattersStats: async () => {
        try {
            const response = await apiClient.get('/matters/stats')
            return response.data
        } catch (error) {
            console.error('Error fetching matters stats:', error)
            throw error
        }
    },

    getMatter: async (matterId: string) => {
        try {
            const response = await apiClient.get(`/matters/${matterId}`)
            return response.data
        } catch (error) {
            console.error('Error fetching matter:', error)
            throw error
        }
    },

    getAITasks: async (limit: number = 10) => {
        try {
            const response = await apiClient.get('/ai-tasks/tasks', { params: { limit } })
            return response.data
        } catch (error) {
            console.error('Error fetching AI tasks:', error)
            throw error
        }
    },

    deleteMatter: async (matterId: string) => {
        try {
            const response = await apiClient.delete(`/matters/${matterId}`)
            return response.data
        } catch (error) {
            console.error('Error deleting matter:', error)
            throw error
        }
    },

    startIntakeWorkflow: async (formData: FormData) => {
        try {
            const response = await apiClient.post('/matters/intake', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 300000, // 5 minutes for LLM processing
            })
            return response.data
        } catch (error) {
            console.error('Error starting intake workflow:', error)
            throw error
        }
    },

    startDraftingWorkflow: async (matter_id: string, data: any) => {
        try {
            const response = await apiClient.post(`/matters/${matter_id}/draft`, data, {
                timeout: 300000, // 5 minutes for multi-agent LLM workflow
            })
            return response.data
        } catch (error) {
            console.error('Error starting drafting workflow:', error)
            throw error
        }
    },

    getMatterDocuments: async (matterId: string) => {
        try {
            const response = await apiClient.get(`/matters/${matterId}/documents`)
            return response.data
        } catch (error) {
            console.error('Error fetching matter documents:', error)
            throw error
        }
    },

    getParallelView: async (matterId: string) => {
        try {
            const response = await apiClient.get(`/matters/${matterId}/parallel-view`)
            return response.data
        } catch (error) {
            console.error('Error fetching parallel view:', error)
            throw error
        }
    },

    // Documents
    uploadDocument: async (file: File, matterId?: string) => {
        try {
            const formData = new FormData()
            formData.append('file', file)
            if (matterId) {
                formData.append('matter_id', matterId)
            }
            const response = await apiClient.post('/documents/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            })
            return response.data
        } catch (error) {
            console.error('Error uploading document:', error)
            throw error
        }
    },

    getDocument: async (docId: string) => {
        try {
            const response = await apiClient.get(`/documents/${docId}`)
            return response.data
        } catch (error) {
            console.error('Error fetching document:', error)
            throw error
        }
    },

    downloadDocument: async (docId: string) => {
        try {
            const response = await apiClient.get(`/documents/${docId}/download`, {
                responseType: 'blob',
            })
            return response.data
        } catch (error) {
            console.error('Error downloading document:', error)
            throw error
        }
    },

    getDocumentPreview: async (docId: string) => {
        try {
            const response = await apiClient.get(`/documents/${docId}/preview`)
            return response.data
        } catch (error) {
            console.error('Error fetching document preview:', error)
            throw error
        }
    },

    // Evidence & Hearing Workflow
    buildEvidencePacket: async (matterId: string, documents: any[] = []) => {
        try {
            const response = await apiClient.post('/evidence/build', {
                matter_id: matterId,
                documents
            }, {
                timeout: 300000, // 5 minutes for evidence processing
            })
            return response.data
        } catch (error) {
            console.error('Error building evidence packet:', error)
            throw error
        }
    },

    prepareHearing: async (matterId: string) => {
        try {
            const response = await apiClient.post('/evidence/hearing', {
                matter_id: matterId
            }, {
                timeout: 300000, // 5 minutes for hearing prep
            })
            return response.data
        } catch (error) {
            console.error('Error preparing hearing:', error)
            throw error
        }
    },

    // Research Workflow
    searchCases: async (query: string, filters?: any) => {
        try {
            const response = await apiClient.post('/research/search', {
                query,
                filters: filters || {},
            })
            return response.data
        } catch (error) {
            console.error('Error searching cases:', error)
            throw error
        }
    },

    // Get cached judgment data for inspection
    getJudgmentCache: async () => {
        try {
            const response = await apiClient.get('/research/judgment-cache', { timeout: 10000 })
            return response.data
        } catch (error) {
            console.error('Error fetching judgment cache:', error)
            throw error
        }
    },

    // Clear Redis search result cache
    clearSearchCache: async () => {
        try {
            const response = await apiClient.delete('/research/search-cache', { timeout: 10000 })
            return response.data
        } catch (error) {
            console.error('Error clearing search cache:', error)
            throw error
        }
    },

    // Poll background judgment fetch status
    getJudgmentFetchStatus: async (query: string) => {
        try {
            const response = await apiClient.get('/research/judgment-fetch-status', {
                params: { query },
                timeout: 5000,
            })
            return response.data
        } catch (error) {
            // Silently fail — polling errors shouldn't bother the user
            return null
        }
    },

    buildArgument: async (matterId: string | null, issues: any[], cases: any[], query?: string) => {
        try {
            const response = await apiClient.post('/research/build-argument', {
                matter_id: matterId,
                issues,
                cases,
                query,
            })
            return response.data
        } catch (error) {
            console.error('Error building argument:', error)
            throw error
        }
    },

    // Evidence & Hearing Workflow
    certifyTranslation: async (matterId: string, documentId: string) => {
        try {
            const response = await apiClient.post(`/matters/${matterId}/certify-translation`, {
                document_id: documentId,
            })
            return response.data
        } catch (error) {
            console.error('Error certifying translation:', error)
            throw error
        }
    },

    getHearingBundle: async (matterId: string) => {
        try {
            const response = await apiClient.get(`/matters/${matterId}/hearing-bundle`)
            return response.data
        } catch (error) {
            console.error('Error fetching hearing bundle:', error)
            throw error
        }
    },

    analyzeCaseStrength: async (matterId: string) => {
        try {
            const response = await apiClient.post(`/matters/${matterId}/analyze-strength`)
            return response.data
        } catch (error) {
            console.error('Error analyzing case strength:', error)
            throw error
        }
    },

    // ==========================================
    // User Settings - Lexis Cookie Management
    // ==========================================

    /**
     * Get current Lexis cookie authentication status
     * @returns Status object with auth method and expiry
     */
    getLexisCookieStatus: async () => {
        try {
            const response = await apiClient.get('/user/lexis-cookies/status')
            return response.data
        } catch (error) {
            console.error('Error fetching cookie status:', error)
            throw error
        }
    },

    /**
     * Validate Lexis cookies before saving
     * @param cookies - Array of cookie objects from browser export
     * @returns Validation result with valid boolean and message
     */
    validateLexisCookies: async (cookies: any[]) => {
        try {
            const response = await apiClient.post('/user/lexis-cookies/validate', {
                cookies
            })
            return response.data
        } catch (error) {
            console.error('Error validating cookies:', error)
            throw error
        }
    },

    /**
     * Save validated cookies to user profile (encrypted)
     * @param cookies - Array of validated cookie objects
     * @returns Success response with expiry timestamp
     */
    saveLexisCookies: async (cookies: any[]) => {
        try {
            const response = await apiClient.post('/user/lexis-cookies/save', {
                cookies
            })
            return response.data
        } catch (error) {
            console.error('Error saving cookies:', error)
            throw error
        }
    },

    /**
     * Clear saved cookies and revert to UM Library auth
     * @returns Success confirmation
     */
    clearLexisCookies: async () => {
        try {
            const response = await apiClient.delete('/user/lexis-cookies')
            return response.data
        } catch (error) {
            console.error('Error clearing cookies:', error)
            throw error
        }
    },
}

// Payments API
export const paymentsApi = {
    createOrder: async (amount: number, currency: string = 'USD', description?: string) => {
        try {
            const response = await apiClient.post('/payments/orders/create', {
                amount,
                currency,
                description
            })
            return response.data
        } catch (error) {
            console.error('Error creating payment order:', error)
            throw error
        }
    },

    captureOrder: async (orderId: string) => {
        try {
            const response = await apiClient.post('/payments/orders/capture', {
                order_id: orderId
            })
            return response.data
        } catch (error) {
            console.error('Error capturing order:', error)
            throw error
        }
    },

    getOrder: async (orderId: string) => {
        try {
            const response = await apiClient.get(`/payments/orders/${orderId}`)
            return response.data
        } catch (error) {
            console.error('Error fetching order:', error)
            throw error
        }
    }
}

// Admin API
export const adminApi = {
    getUsers: async (page: number = 1, perPage: number = 20) => {
        try {
            const response = await apiClient.get('/admin/users', {
                params: { page, per_page: perPage }
            })
            return response.data
        } catch (error) {
            console.error('Error fetching users:', error)
            throw error
        }
    },

    createUser: async (data: SignupData & { is_superuser?: boolean }) => {
        try {
            const response = await apiClient.post('/admin/users', data)
            return response.data
        } catch (error) {
            console.error('Error creating user:', error)
            throw error
        }
    },

    getStatistics: async () => {
        try {
            const response = await apiClient.get('/admin/statistics')
            return response.data
        } catch (error) {
            console.error('Error fetching statistics:', error)
            throw error
        }
    }
}

// Subscription API (Usage tracking and payment gate)
export interface UsageStatus {
    id: string
    user_id: string
    has_paid: boolean
    subscription_status: string | null
    usage: {
        intake: { used: number; limit: number | string; remaining: number | string }
        drafting: { used: number; limit: number | string; remaining: number | string }
        evidence: { used: number; limit: number | string; remaining: number | string }
        research: { used: number; limit: number | string; remaining: number | string }
    }
    created_at: string
    updated_at: string
}

export interface WorkflowAccess {
    workflow_type: string
    can_access: boolean
    remaining_free_uses: number | string
    has_subscription: boolean
    requires_payment: boolean
}

export const subscriptionApi = {
    // Get current usage status for the user
    getUsageStatus: async (): Promise<UsageStatus> => {
        try {
            const response = await apiClient.get('/subscription/usage/status')
            return response.data
        } catch (error) {
            console.error('Error fetching usage status:', error)
            throw error
        }
    },

    // Check if user can access a specific workflow
    checkWorkflowAccess: async (workflowType: string): Promise<WorkflowAccess> => {
        try {
            const response = await apiClient.get(`/subscription/check/${workflowType}`)
            return response.data
        } catch (error) {
            console.error('Error checking workflow access:', error)
            throw error
        }
    },

    // Activate subscription after successful payment
    activateSubscription: async (subscriptionId: string): Promise<{ status: string; message: string }> => {
        try {
            const response = await apiClient.post('/subscription/activate', {
                subscription_id: subscriptionId
            })
            return response.data
        } catch (error) {
            console.error('Error activating subscription:', error)
            throw error
        }
    },

    // Cancel subscription
    cancelSubscription: async (): Promise<{ status: string; message: string }> => {
        try {
            const response = await apiClient.post('/subscription/cancel')
            return response.data
        } catch (error) {
            console.error('Error canceling subscription:', error)
            throw error
        }
    },
}

export default api