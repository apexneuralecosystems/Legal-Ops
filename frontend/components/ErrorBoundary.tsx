'use client'

import React, { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import Link from 'next/link'

interface Props {
    children: ReactNode
    fallback?: ReactNode
}

interface State {
    hasError: boolean
    error: Error | null
    errorInfo: React.ErrorInfo | null
}

/**
 * Error Boundary component that catches JavaScript errors anywhere in their
 * child component tree, logs those errors, and displays a fallback UI.
 */
export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props)
        this.state = { hasError: false, error: null, errorInfo: null }
    }

    static getDerivedStateFromError(error: Error): State {
        // Update state so the next render will show the fallback UI
        return { hasError: true, error, errorInfo: null }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        // Log the error to console (in production, send to error tracking service)
        console.error('Error Boundary caught an error:', error, errorInfo)
        this.setState({ errorInfo })
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null })
    }

    render() {
        if (this.state.hasError) {
            // Custom fallback UI
            if (this.props.fallback) {
                return this.props.fallback
            }

            return (
                <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                    <div className="glass-card max-w-md w-full p-8 text-center">
                        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertTriangle className="w-8 h-8 text-red-600" />
                        </div>

                        <h1 className="text-2xl font-bold text-gray-900 mb-2">
                            Something went wrong
                        </h1>

                        <p className="text-gray-600 mb-6">
                            An unexpected error occurred. Please try again or return to the dashboard.
                        </p>

                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <div className="mb-6 p-4 bg-red-50 rounded-lg text-left overflow-auto">
                                <p className="text-sm font-mono text-red-800 break-words">
                                    {this.state.error.message}
                                </p>
                                {this.state.errorInfo && (
                                    <pre className="mt-2 text-xs text-red-600 whitespace-pre-wrap">
                                        {this.state.errorInfo.componentStack}
                                    </pre>
                                )}
                            </div>
                        )}

                        <div className="flex gap-3 justify-center">
                            <button
                                onClick={this.handleReset}
                                className="btn-primary flex items-center gap-2"
                            >
                                <RefreshCw className="w-4 h-4" />
                                Try Again
                            </button>

                            <Link
                                href="/dashboard"
                                className="px-6 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
                            >
                                <Home className="w-4 h-4" />
                                Dashboard
                            </Link>
                        </div>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}
