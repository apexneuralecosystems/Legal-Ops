import './globals.css'
import type { Metadata } from 'next'
import { Source_Sans_3, Merriweather } from 'next/font/google'
import { Providers } from './providers'
import ErrorBoundary from '@/components/ErrorBoundary'
import PaymentGateModal from '@/components/PaymentGateModal'

const sourceSans = Source_Sans_3({ subsets: ['latin'], variable: '--font-sans' })
const merriweather = Merriweather({
    subsets: ['latin'],
    variable: '--font-serif',
    weight: ['400', '700', '900']
})

export const metadata: Metadata = {
    metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
    title: 'Malaysian Legal AI Agent',
    description: 'Multi-agent system for legal document processing with bilingual support',
    openGraph: {
        title: 'Malaysian Legal AI Agent',
        description: 'Multi-agent system for legal document processing with bilingual support',
        type: 'website',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'Malaysian Legal AI Agent',
        description: 'Multi-agent system for legal document processing with bilingual support',
    },
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className="dark" suppressHydrationWarning>
            <body className={`${sourceSans.variable} ${merriweather.variable}`}>
                <Providers>
                    <ErrorBoundary>
                        {children}
                        <PaymentGateModal />
                    </ErrorBoundary>
                </Providers>
            </body>
        </html>
    )
}