'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, tokenManager, UserInfo, AuthTokens, SignupData, LoginData, ApiError } from './api'

interface AuthState {
    user: UserInfo | null
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null

    // Actions
    login: (data: LoginData) => Promise<boolean>
    signup: (data: SignupData) => Promise<boolean>
    logout: () => void
    clearError: () => void
    checkAuth: () => void
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,

            login: async (data: LoginData): Promise<boolean> => {
                set({ isLoading: true, error: null })

                try {
                    const tokens = await authApi.login(data)

                    if (tokens.access_token) {
                        set({
                            isAuthenticated: true,
                            isLoading: false,
                            user: {
                                id: '',
                                email: data.email,
                                is_active: true
                            }
                        })
                        return true
                    }

                    set({ isLoading: false })
                    return false
                } catch (error) {
                    const apiError = error as ApiError
                    set({
                        isLoading: false,
                        error: apiError.message || 'Login failed. Please check your credentials.'
                    })
                    return false
                }
            },

            signup: async (data: SignupData): Promise<boolean> => {
                set({ isLoading: true, error: null })

                try {
                    const user = await authApi.signup(data)

                    if (user.id) {
                        // Auto-login after signup
                        const loginSuccess = await get().login({
                            email: data.email,
                            password: data.password
                        })
                        return loginSuccess
                    }

                    set({ isLoading: false })
                    return false
                } catch (error) {
                    const apiError = error as ApiError
                    set({
                        isLoading: false,
                        error: apiError.message || 'Signup failed. Please try again.'
                    })
                    return false
                }
            },

            logout: () => {
                authApi.logout()
                set({
                    user: null,
                    isAuthenticated: false,
                    error: null
                })
            },

            clearError: () => {
                set({ error: null })
            },

            checkAuth: () => {
                const isAuth = tokenManager.isAuthenticated()
                if (!isAuth) {
                    set({ isAuthenticated: false, user: null })
                }
            }
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user,
                isAuthenticated: state.isAuthenticated
            })
        }
    )
)

export default useAuthStore
