'use client'

import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { ChevronDown, ChevronUp, MessageSquare, Flag, ArrowRight } from 'lucide-react'

interface ParallelViewerProps {
    matterId: string
}

interface Segment {
    segment_id: string
    doc_id: string
    page: number
    sequence: number
    text: string
    lang: string
    lang_confidence: number
    ocr_confidence: number
    translation_en?: string
    translation_ms?: string
    translation_literal?: string
    translation_idiomatic?: string
    alignment_score?: number
    human_check_required: boolean
    flagged_for_review: boolean
}

export default function ParallelViewer({ matterId }: ParallelViewerProps) {
    const [confidenceFilter, setConfidenceFilter] = useState(0.0)
    const [selectedSegment, setSelectedSegment] = useState<string | null>(null)
    const [showComments, setShowComments] = useState(false)

    const { data, isLoading } = useQuery({
        queryKey: ['parallel-view', matterId],
        queryFn: async () => {
            const { api } = await import('@/lib/api')
            return api.getParallelView(matterId)
        },
    })

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        )
    }

    const parallelSegments = data?.parallel_segments || {}
    const allSegments: Segment[] = (Object.values(parallelSegments) as Segment[][]).flat()

    // Filter by confidence
    const filteredSegments = allSegments.filter(
        (seg) => (seg.lang_confidence || 1.0) >= confidenceFilter
    )

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.9) return 'text-green-600'
        if (confidence >= 0.7) return 'text-yellow-600'
        return 'text-red-600'
    }

    const handleFlagForReview = (segmentId: string) => {
        // TODO: API call to flag segment
        console.log('Flagging segment for review:', segmentId)
    }

    return (
        <div className="space-y-6">
            {/* Header & Filters */}
            <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold">Parallel Text Viewer</h2>
                    <div className="flex items-center gap-4">
                        <label className="text-sm text-gray-600">
                            Min Confidence:
                            <select
                                value={confidenceFilter}
                                onChange={(e) => setConfidenceFilter(parseFloat(e.target.value))}
                                className="ml-2 border border-gray-300 rounded px-2 py-1"
                            >
                                <option value="0.0">All</option>
                                <option value="0.5">≥ 50%</option>
                                <option value="0.7">≥ 70%</option>
                                <option value="0.9">≥ 90%</option>
                            </select>
                        </label>
                        <div className="text-sm text-gray-600">
                            {filteredSegments.length} segments
                        </div>
                    </div>
                </div>

                {/* Legend */}
                <div className="flex gap-4 text-xs text-gray-600">
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-green-100 border border-green-300 rounded"></div>
                        <span>High confidence (≥90%)</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-yellow-100 border border-yellow-300 rounded"></div>
                        <span>Medium confidence (70-89%)</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-red-100 border border-red-300 rounded"></div>
                        <span>Low confidence (&lt;70%)</span>
                    </div>
                </div>
            </div>

            {/* Parallel Segments */}
            <div className="space-y-4">
                {filteredSegments.map((segment) => {
                    const isExpanded = selectedSegment === segment.segment_id
                    const confidence = segment.lang_confidence || 1.0
                    const bgColor =
                        confidence >= 0.9
                            ? 'bg-green-50 border-green-200'
                            : confidence >= 0.7
                                ? 'bg-yellow-50 border-yellow-200'
                                : 'bg-red-50 border-red-200'

                    return (
                        <div
                            key={segment.segment_id}
                            className={`border rounded-lg overflow-hidden ${bgColor}`}
                        >
                            {/* Segment Header */}
                            <div className="p-4 flex items-center justify-between bg-white bg-opacity-50">
                                <div className="flex items-center gap-4">
                                    <span className="text-xs font-mono text-gray-500">
                                        {segment.segment_id}
                                    </span>
                                    <span className="text-xs text-gray-600">
                                        Page {segment.page} • Seq {segment.sequence}
                                    </span>
                                    <span className={`text-xs font-semibold ${getConfidenceColor(confidence)}`}>
                                        {Math.round(confidence * 100)}% confidence
                                    </span>
                                    {segment.human_check_required && (
                                        <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                                            Review Required
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => handleFlagForReview(segment.segment_id)}
                                        className="text-gray-500 hover:text-red-600 transition-colors"
                                        title="Flag for review"
                                    >
                                        <Flag className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() =>
                                            setSelectedSegment(isExpanded ? null : segment.segment_id)
                                        }
                                        className="text-gray-500 hover:text-gray-700"
                                    >
                                        {isExpanded ? (
                                            <ChevronUp className="w-5 h-5" />
                                        ) : (
                                            <ChevronDown className="w-5 h-5" />
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Dual Pane Content */}
                            <div className="grid md:grid-cols-2 gap-4 p-4">
                                {/* Malay/Source */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <h4 className="text-sm font-semibold text-gray-700">
                                            {segment.lang === 'ms' ? 'Malay (Original)' : 'Source'}
                                        </h4>
                                        <span className="text-xs text-gray-500 uppercase">
                                            {segment.lang}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-800 leading-relaxed">
                                        {segment.text}
                                    </p>
                                </div>

                                {/* English/Translation */}
                                <div className="space-y-2 border-l-2 border-gray-200 pl-4">
                                    <div className="flex items-center justify-between">
                                        <h4 className="text-sm font-semibold text-gray-700">
                                            {segment.lang === 'en' ? 'English (Original)' : 'Translation'}
                                        </h4>
                                        {segment.alignment_score && (
                                            <span className="text-xs text-gray-500">
                                                Alignment: {Math.round(segment.alignment_score * 100)}%
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-sm text-gray-800 leading-relaxed">
                                        {segment.lang === 'ms'
                                            ? segment.translation_en || '[Translation pending]'
                                            : segment.translation_ms || segment.text}
                                    </p>
                                </div>
                            </div>

                            {/* Expanded Details */}
                            {isExpanded && (
                                <div className="border-t border-gray-200 bg-white bg-opacity-70 p-4 space-y-3">
                                    {/* Literal vs Idiomatic */}
                                    {segment.translation_literal && segment.translation_idiomatic && (
                                        <div className="grid md:grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <h5 className="font-semibold text-gray-600 mb-1">
                                                    Literal Translation
                                                </h5>
                                                <p className="text-gray-700">{segment.translation_literal}</p>
                                            </div>
                                            <div>
                                                <h5 className="font-semibold text-gray-600 mb-1">
                                                    Idiomatic Translation
                                                </h5>
                                                <p className="text-gray-700">{segment.translation_idiomatic}</p>
                                            </div>
                                        </div>
                                    )}

                                    {/* Metadata */}
                                    <div className="flex gap-6 text-xs text-gray-600">
                                        <div>
                                            <span className="font-semibold">OCR Confidence:</span>{' '}
                                            {Math.round((segment.ocr_confidence || 1.0) * 100)}%
                                        </div>
                                        <div>
                                            <span className="font-semibold">Language Confidence:</span>{' '}
                                            {Math.round(confidence * 100)}%
                                        </div>
                                        <div>
                                            <span className="font-semibold">Document:</span> {segment.doc_id}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2 pt-2">
                                        <button className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors">
                                            Send to Translator
                                        </button>
                                        <button className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors flex items-center gap-1">
                                            <MessageSquare className="w-3 h-3" />
                                            Add Comment
                                        </button>
                                        <button className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors flex items-center gap-1">
                                            <ArrowRight className="w-3 h-3" />
                                            Jump to Draft
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>

            {filteredSegments.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                    No segments match the current filter criteria
                </div>
            )}
        </div>
    )
}
