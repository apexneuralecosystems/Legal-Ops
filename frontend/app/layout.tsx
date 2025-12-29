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
    metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:8006'),
    title: 'ApexNeural Legal Ops',
    description: 'AI-powered legal operations platform for automated intake, drafting, and research',
    openGraph: {
        title: 'ApexNeural Legal Ops',
        description: 'AI-powered legal operations platform for automated intake, drafting, and research',
        type: 'website',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'ApexNeural Legal Ops',
        description: 'AI-powered legal operations platform for automated intake, drafting, and research',
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