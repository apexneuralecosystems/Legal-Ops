'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/authStore'
import { authApi, tokenManager } from '@/lib/api'

interface ProtectedRouteProps {
    children: React.ReactNode
    fallback?: React.ReactNode
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
    const router = useRouter()
    const { isAuthenticated, checkAuth, logout } = useAuthStore()
    const [isChecking, setIsChecking] = useState(true)

    useEffect(() => {
        let isMounted = true
        const validate = async () => {
            const token = tokenManager.getAccessToken()

            if (!token) {
                router.push('/login')
                return
            }

            const isValid = await authApi.verifyToken(token)
            if (!isValid) {
                logout()
                router.push('/login')
                return
            }

            checkAuth()
            if (isMounted) setIsChecking(false)
        }

        validate()
        return () => {
            isMounted = false
        }
    }, [router, checkAuth, logout])

    // Show loading while checking auth
    if (isChecking) {
        return fallback || (
            <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--accent-gold)] mx-auto"></div>
                    <p className="mt-4 text-gray-500 font-bold uppercase tracking-widest text-xs">Verifying Credentials...</p>
                </div>
            </div>
        )
    }

    // Redirect if not authenticated
    if (!isAuthenticated && !tokenManager.isAuthenticated()) {
        return null
    }

    return <>{children}</>
}

// HOC version for class components
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
    return function AuthenticatedComponent(props: P) {
        return (
            <ProtectedRoute>
                <Component {...props} />
            </ProtectedRoute>
        )
    }
}

export default ProtectedRoute
