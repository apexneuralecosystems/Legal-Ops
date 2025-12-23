'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { FileText, CheckCircle, AlertCircle, Loader2, Eye, Download } from 'lucide-react'
import { api } from '@/lib/api'

interface DraftingFlowProps {
    matterId: string
    matterSnapshot: any
}

export default function DraftingFlow({ matterId, matterSnapshot }: DraftingFlowProps) {
    const [currentStep, setCurrentStep] = useState(1)
    const [selectedIssues, setSelectedIssues] = useState<any[]>([])
    const [selectedPrayers, setSelectedPrayers] = useState<any[]>([])
    const [templateId, setTemplateId] = useState('TPL-HighCourt-MS-v2')
    const [draftedPleading, setDraftedPleading] = useState<any>(null)

    // Step 1: Issue Planning
    const issuePlannerQuery = useQuery({
        queryKey: ['issue-planner', matterId],
        queryFn: async () => {
            // Mock data - in production, call issue planner agent
            return {
                issues: [
                    {
                        id: 'ISS-01',
                        title: 'Breach of contract - non-payment',
                        legal_basis: ['Contract Act 1950 s.40', 'Common law'],
                        theory: 'primary',
                        confidence: 0.92,
                        likely_evidence_required: ['Contract document', 'Payment records'],
                        template_id: 'TPL-PRAYER-MONEY',
                    },
                    {
                        id: 'ISS-02',
                        title: 'Damages for breach',
                        legal_basis: ['Contract Act 1950 s.74', 'Hadley v Baxendale'],
                        theory: 'primary',
                        confidence: 0.88,
                        likely_evidence_required: ['Loss calculations', 'Invoices'],
                        template_id: 'TPL-PRAYER-MONEY',
                    },
                ],
                suggested_prayers: [
                    {
                        text_en: 'Judgment for the sum of RM 120,000',
                        text_ms: 'Penghakiman untuk jumlah RM 120,000',
                        template_id: 'TPL-PRAYER-MONEY',
                        priority: 'primary',
                        confidence: 0.95,
                    },
                    {
                        text_en: 'Interest at 5% per annum',
                        text_ms: 'Faedah pada kadar 5% setahun',
                        template_id: 'TPL-PRAYER-INTEREST',
                        priority: 'primary',
                        confidence: 0.90,
                    },
                    {
                        text_en: 'Costs and other relief',
                        text_ms: 'Kos dan relief lain',
                        template_id: 'TPL-PRAYER-COSTS',
                        priority: 'alternative',
                        confidence: 0.98,
                    },
                ],
            }
        },
        enabled: currentStep === 1,
    })

    // Step 3: Drafting
    const draftingMutation = useMutation({
        mutationFn: async () => {
            return api.startDraftingWorkflow(matterId, {
                template_id: templateId,
                issues_selected: selectedIssues,
                prayers_selected: selectedPrayers,
            })
        },
        onSuccess: (data) => {
            setDraftedPleading(data.workflow_result)
            setCurrentStep(3)
        },
    })

    const toggleIssue = (issue: any) => {
        setSelectedIssues((prev) =>
            prev.find((i) => i.id === issue.id)
                ? prev.filter((i) => i.id !== issue.id)
                : [...prev, issue]
        )
    }

    const togglePrayer = (prayer: any) => {
        setSelectedPrayers((prev) =>
            prev.find((p) => p.text_en === prayer.text_en)
                ? prev.filter((p) => p.text_en !== prayer.text_en)
                : [...prev, prayer]
        )
    }

    const handleNext = () => {
        if (currentStep === 1) {
            setCurrentStep(2)
        } else if (currentStep === 2) {
            draftingMutation.mutate()
        }
    }

    return (
        <div className="space-y-6">
            {/* Progress Steps */}
            <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between">
                    {[
                        { num: 1, label: 'Select Issues & Prayers' },
                        { num: 2, label: 'Choose Template' },
                        { num: 3, label: 'Review Draft' },
                    ].map((step, idx) => (
                        <div key={step.num} className="flex items-center flex-1">
                            <div className="flex items-center gap-3">
                                <div
                                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${currentStep >= step.num
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-200 text-gray-600'
                                        }`}
                                >
                                    {currentStep > step.num ? (
                                        <CheckCircle className="w-6 h-6" />
                                    ) : (
                                        step.num
                                    )}
                                </div>
                                <span
                                    className={`text-sm font-medium ${currentStep >= step.num ? 'text-gray-900' : 'text-gray-500'
                                        }`}
                                >
                                    {step.label}
                                </span>
                            </div>
                            {idx < 2 && (
                                <div
                                    className={`flex-1 h-1 mx-4 ${currentStep > step.num ? 'bg-blue-600' : 'bg-gray-200'
                                        }`}
                                />
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Step 1: Issue & Prayer Selection */}
            {currentStep === 1 && (
                <div className="grid md:grid-cols-2 gap-6">
                    {/* Issues */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <h2 className="text-lg font-semibold mb-4">Legal Issues</h2>
                        {issuePlannerQuery.isLoading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {issuePlannerQuery.data?.issues.map((issue: any) => (
                                    <div
                                        key={issue.id}
                                        onClick={() => toggleIssue(issue)}
                                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${selectedIssues.find((i) => i.id === issue.id)
                                                ? 'border-blue-600 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <h3 className="font-semibold text-gray-900">{issue.title}</h3>
                                            <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                                {Math.round(issue.confidence * 100)}%
                                            </span>
                                        </div>
                                        <div className="text-sm text-gray-600 space-y-1">
                                            <p>
                                                <span className="font-medium">Legal Basis:</span>{' '}
                                                {issue.legal_basis.join(', ')}
                                            </p>
                                            <p>
                                                <span className="font-medium">Theory:</span> {issue.theory}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Prayers */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <h2 className="text-lg font-semibold mb-4">Prayers</h2>
                        {issuePlannerQuery.isLoading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {issuePlannerQuery.data?.suggested_prayers.map((prayer: any, idx: number) => (
                                    <div
                                        key={idx}
                                        onClick={() => togglePrayer(prayer)}
                                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${selectedPrayers.find((p) => p.text_en === prayer.text_en)
                                                ? 'border-blue-600 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                                                {prayer.priority}
                                            </span>
                                            <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                                {Math.round(prayer.confidence * 100)}%
                                            </span>
                                        </div>
                                        <p className="text-sm font-medium text-gray-900 mb-1">
                                            {prayer.text_ms}
                                        </p>
                                        <p className="text-xs text-gray-600">{prayer.text_en}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Step 2: Template Selection */}
            {currentStep === 2 && (
                <div className="bg-white rounded-lg shadow-sm p-6">
                    <h2 className="text-lg font-semibold mb-4">Choose Pleading Template</h2>
                    <div className="grid md:grid-cols-3 gap-4">
                        {[
                            {
                                id: 'TPL-HighCourt-MS-v2',
                                name: 'High Court Malay',
                                court: 'High Court in Malaya',
                                language: 'Malay',
                            },
                            {
                                id: 'TPL-HighCourt-EN-v2',
                                name: 'High Court English',
                                court: 'High Court (East Malaysia)',
                                language: 'English',
                            },
                            {
                                id: 'TPL-SessionsCourt-MS-v1',
                                name: 'Sessions Court Malay',
                                court: 'Sessions Court',
                                language: 'Malay',
                            },
                        ].map((template) => (
                            <div
                                key={template.id}
                                onClick={() => setTemplateId(template.id)}
                                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${templateId === template.id
                                        ? 'border-blue-600 bg-blue-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                    }`}
                            >
                                <FileText className="w-8 h-8 text-gray-400 mb-3" />
                                <h3 className="font-semibold text-gray-900 mb-2">{template.name}</h3>
                                <p className="text-sm text-gray-600 mb-1">{template.court}</p>
                                <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                    {template.language}
                                </span>
                            </div>
                        ))}
                    </div>

                    {/* Summary */}
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">Summary</h3>
                        <div className="text-sm text-gray-600 space-y-1">
                            <p>
                                <span className="font-medium">Issues Selected:</span> {selectedIssues.length}
                            </p>
                            <p>
                                <span className="font-medium">Prayers Selected:</span> {selectedPrayers.length}
                            </p>
                            <p>
                                <span className="font-medium">Template:</span> {templateId}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Step 3: Review Draft */}
            {currentStep === 3 && draftedPleading && (
                <div className="space-y-6">
                    {/* Dual Pane Editor */}
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Malay Draft */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">Malay Pleading</h2>
                                <div className="flex gap-2">
                                    <button className="text-sm px-3 py-1 bg-gray-100 rounded hover:bg-gray-200">
                                        <Eye className="w-4 h-4 inline mr-1" />
                                        Preview
                                    </button>
                                    <button className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                                        <Download className="w-4 h-4 inline mr-1" />
                                        Download
                                    </button>
                                </div>
                            </div>
                            <div className="prose prose-sm max-w-none">
                                <pre className="whitespace-pre-wrap text-sm font-mono bg-gray-50 p-4 rounded border border-gray-200">
                                    {draftedPleading.pleading_ms?.pleading_ms_text || 'Loading...'}
                                </pre>
                            </div>
                        </div>

                        {/* English Companion */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">English Companion</h2>
                                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                                    For Internal Review Only
                                </span>
                            </div>
                            <div className="prose prose-sm max-w-none">
                                <pre className="whitespace-pre-wrap text-sm font-mono bg-gray-50 p-4 rounded border border-gray-200">
                                    {draftedPleading.pleading_en?.pleading_en_text || '[English companion pending]'}
                                </pre>
                            </div>
                        </div>
                    </div>

                    {/* QA Report */}
                    {draftedPleading.qa_report && (
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h2 className="text-lg font-semibold mb-4">Consistency QA Report</h2>
                            {draftedPleading.qa_report.block_for_human ? (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                                    <div className="flex items-start gap-3">
                                        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                                        <div>
                                            <h3 className="font-semibold text-red-900 mb-1">
                                                Human Review Required
                                            </h3>
                                            <p className="text-sm text-red-800">
                                                High severity issues detected. Please review before proceeding.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                                    <div className="flex items-start gap-3">
                                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                                        <div>
                                            <h3 className="font-semibold text-green-900 mb-1">
                                                QA Passed
                                            </h3>
                                            <p className="text-sm text-green-800">
                                                No critical issues detected. Ready for review.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between">
                <button
                    onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
                    disabled={currentStep === 1}
                    className="px-6 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Back
                </button>
                <button
                    onClick={handleNext}
                    disabled={
                        (currentStep === 1 && (selectedIssues.length === 0 || selectedPrayers.length === 0)) ||
                        draftingMutation.isPending
                    }
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {draftingMutation.isPending ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Drafting...
                        </>
                    ) : currentStep === 3 ? (
                        'Finalize'
                    ) : (
                        'Next'
                    )}
                </button>
            </div>
        </div>
    )
}
