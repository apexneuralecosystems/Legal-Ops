'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/authStore'
import { tokenManager } from '@/lib/api'

interface ProtectedRouteProps {
    children: React.ReactNode
    fallback?: React.ReactNode
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
    const router = useRouter()
    const { isAuthenticated, checkAuth } = useAuthStore()
    const [isChecking, setIsChecking] = useState(true)

    useEffect(() => {
        // Check if user has valid token
        const hasToken = tokenManager.isAuthenticated()

        if (!hasToken) {
            router.push('/login')
            return
        }

        checkAuth()
        setIsChecking(false)
    }, [router, checkAuth])

    // Show loading while checking auth
    if (isChecking) {
        return fallback || (
            <div className="min-h-screen flex items-center justify-center bg-slate-900">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="mt-4 text-slate-400">Loading...</p>
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
