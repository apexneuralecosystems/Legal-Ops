import { AlertCircle, FileText, Scale } from 'lucide-react'
import Link from 'next/link'

interface MatterCardProps {
    matter: {
        matter_id: string
        title: string
        status: string
        court?: string
        jurisdiction?: string
        primary_language: string
        risk_scores?: {
            composite_score: number
            jurisdictional_complexity: number
            language_complexity: number
            volume_risk: number
            time_pressure: number
        }
        human_review_required: boolean
        parties?: Array<{ role: string; name: string }>
    }
}

export default function MatterCard({ matter }: MatterCardProps) {
    const getRiskColor = (score: number) => {
        if (score >= 4) return 'risk-high'
        if (score >= 3) return 'risk-medium'
        return 'risk-low'
    }

    const getRiskLabel = (score: number) => {
        if (score >= 4) return 'High Risk'
        if (score >= 3) return 'Medium Risk'
        return 'Low Risk'
    }

    const compositeScore = matter.risk_scores?.composite_score || 0

    return (
        <Link href={`/matter/${matter.matter_id}`}>
            <div className="matter-card">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">
                            {matter.title}
                        </h3>
                        <p className="text-sm text-gray-500">{matter.matter_id}</p>
                    </div>
                    {matter.human_review_required && (
                        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 ml-2" />
                    )}
                </div>

                {/* Parties */}
                {matter.parties && matter.parties.length > 0 && (
                    <div className="mb-4 text-sm">
                        <div className="flex items-start gap-2">
                            <Scale className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                                {matter.parties.slice(0, 2).map((party, idx) => (
                                    <div key={idx} className="text-gray-700">
                                        <span className="font-medium capitalize">{party.role}:</span> {party.name}
                                    </div>
                                ))}
                                {matter.parties.length > 2 && (
                                    <div className="text-gray-500 text-xs mt-1">
                                        +{matter.parties.length - 2} more
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Court & Jurisdiction */}
                <div className="mb-4 space-y-1 text-sm">
                    {matter.court && (
                        <div className="text-gray-600">
                            <span className="font-medium">Court:</span> {matter.court}
                        </div>
                    )}
                    {matter.jurisdiction && (
                        <div className="text-gray-600">
                            <span className="font-medium">Jurisdiction:</span> {matter.jurisdiction}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <div className="flex items-center gap-2">
                        <span className={`risk-badge ${getRiskColor(compositeScore)}`}>
                            {getRiskLabel(compositeScore)}
                        </span>
                        <span className="text-xs text-gray-500 uppercase font-medium">
                            {matter.primary_language === 'ms' ? 'Malay' : 'English'}
                        </span>
                    </div>
                    <span className="text-xs text-gray-500 uppercase font-medium px-2 py-1 bg-gray-100 rounded">
                        {matter.status}
                    </span>
                </div>

                {/* Risk Details (if available) */}
                {matter.risk_scores && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                                <span className="text-gray-500">Jurisdictional:</span>
                                <span className="ml-1 font-medium">{matter.risk_scores.jurisdictional_complexity}/5</span>
                            </div>
                            <div>
                                <span className="text-gray-500">Language:</span>
                                <span className="ml-1 font-medium">{matter.risk_scores.language_complexity}/5</span>
                            </div>
                            <div>
                                <span className="text-gray-500">Volume:</span>
                                <span className="ml-1 font-medium">{matter.risk_scores.volume_risk}/5</span>
                            </div>
                            <div>
                                <span className="text-gray-500">Time:</span>
                                <span className="ml-1 font-medium">{matter.risk_scores.time_pressure}/5</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Link>
    )
}
