'use client'

import { useEffect } from 'react'
import { RotateCw, AlertTriangle } from 'lucide-react'

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string }
    reset: () => void
}) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error(error)

        // Check for version mismatch patterns
        const isVersionMismatch =
            error.message.includes("Failed to find Server Action") ||
            error.message.includes("Loading chunk") ||
            error.message.includes("minified React error");

        if (isVersionMismatch) {
            // Automatically reload once if it's a version mismatch
            // Use sessionStorage to prevent infinite loops
            const hasReloaded = sessionStorage.getItem('auto_reloaded');
            if (!hasReloaded) {
                sessionStorage.setItem('auto_reloaded', 'true');
                window.location.reload();
            }
        }
    }, [error])

    return (
        <html>
            <body className="bg-[var(--bg-primary)] text-[var(--text-primary)] min-h-screen flex items-center justify-center p-6">
                <div className="max-w-md w-full p-8 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-primary)] shadow-2xl text-center">
                    <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-400/10 flex items-center justify-center">
                        <AlertTriangle className="w-8 h-8 text-red-400" />
                    </div>

                    <h2 className="text-2xl font-bold mb-3 gradient-text">Application Error</h2>
                    <p className="text-[var(--text-secondary)] mb-8 text-sm leading-relaxed">
                        We encountered an unexpected issue. This might be due to a new update.
                    </p>

                    <button
                        onClick={() => {
                            sessionStorage.removeItem('auto_reloaded');
                            // Try to reset via Next.js first, then hard reload if needed
                            reset();
                            setTimeout(() => window.location.reload(), 100);
                        }}
                        className="w-full btn-primary py-3 flex items-center justify-center gap-2"
                    >
                        <RotateCw className="w-4 h-4" />
                        Reload Application
                    </button>

                    {process.env.NODE_ENV === 'development' && (
                        <div className="mt-8 p-4 rounded-lg bg-[var(--bg-tertiary)] text-left overflow-auto max-h-40">
                            <p className="text-xs font-mono text-red-300 break-words">{error.message}</p>
                            {error.digest && <p className="text-xs text-[var(--text-tertiary)] mt-1">Digest: {error.digest}</p>}
                        </div>
                    )}
                </div>
            </body>
        </html>
    )
}
