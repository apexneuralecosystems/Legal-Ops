/**
 * TypeScript type definitions for API responses.
 * These provide type safety and IDE autocompletion for API data.
 */

// Matter types
export interface Matter {
    id: string
    matter_id: string
    title: string
    status: 'intake' | 'drafting' | 'research' | 'evidence' | 'hearing' | 'filed' | 'closed'
    court?: string
    jurisdiction?: string
    language?: 'ms' | 'en' | 'bilingual'
    parties?: PartyInfo
    risk_scores?: RiskScores
    issues?: Issue[]
    prayers?: Prayer[]
    document_count?: number
    translation_completed?: boolean
    requires_human_review?: boolean
    created_at: string
    updated_at: string
}

export interface PartyInfo {
    plaintiff?: string
    defendant?: string
    [key: string]: string | undefined
}

export interface RiskScores {
    overall: number
    procedural: number
    substantive: number
    [key: string]: number
}

export interface Issue {
    id: string
    title: string
    legal_basis: string[]
    theory: 'primary' | 'alternative'
    confidence: number
}

export interface Prayer {
    text_en: string
    text_ms: string
    priority: 'primary' | 'alternative'
    confidence: number
}

// AI Task types
export interface AITask {
    id: string
    matter_id: string
    agent: string
    type: string
    status: 'pending' | 'in_progress' | 'completed' | 'failed'
    description: string
    progress?: number
    started_at?: string
    completed_at?: string
}

export interface AITasksResponse {
    tasks: AITask[]
    total: number
    last_updated: string
}

// Document types
export interface Document {
    id: string
    matter_id: string
    filename: string
    original_filename: string
    mime_type: string
    file_size: number
    source: 'upload' | 'email' | 'ocr'
    ocr_completed: boolean
    ocr_confidence?: number
    detected_language?: string
    created_at: string
}

// Research types
export interface CaseResult {
    title: string
    citation: string
    court: string
    year?: number
    headnote_en?: string
    headnote_ms?: string
    relevance_score: number
    binding: boolean
    url?: string
}

export interface ResearchResponse {
    cases: CaseResult[]
    total_results: number
    live_data: boolean
    data_source: 'commonlii' | 'mock'
}

// Drafting types
export interface DraftingWorkflowInput {
    template_id: string
    issues_selected: Issue[]
    prayers_selected: Prayer[]
}

export interface PleadingDraft {
    pleading_ms_text: string
    pleading_en_text?: string
}

export interface DraftingWorkflowResult {
    pleading_ms?: PleadingDraft
    pleading_en?: PleadingDraft
    qa_report?: {
        block_for_human: boolean
        issues: string[]
    }
}

// Evidence types
export interface EvidencePacket {
    packet_id: string
    documents: Document[]
    created_at: string
}

export interface HearingBundle {
    bundle_id: string
    content: string
    generated_at: string
}

// API Response wrappers
export interface APIResponse<T> {
    status: 'success' | 'error'
    data?: T
    message?: string
    error?: string
}

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    per_page: number
    total_pages: number
}
