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

// Phase 2: Knowledge Base Insights
export interface KBInsights {
    kb_available: boolean
    similar_matters_count: number
    success_patterns?: Array<{
        description: string
        confidence: number
        frequency: number
        pattern_type?: string
    }>
    risk_factors?: Array<{
        description: string
        severity: string
        frequency?: number
    }>
    outcome_prediction?: {
        predicted_outcome: string
        confidence: number
        reasoning?: string
    }
    strategic_recommendations?: string[]
    similar_matters?: any[]
    additional_cases?: any[]
    insights?: any
}

// Phase 3: Cache Statistics
export interface CacheStatistics {
    cache_hits: number
    total_cases: number
    time_saved: number
    cache_hit_rate?: number
}

// Argument Building Response
export interface ArgumentResponse {
    status: string
    argument_memo: {
        issue_memo_en: string
        issue_memo_ms: string
        suggested_wording?: Array<{
            wording_en: string
            wording_ms: string
            binding_authorities?: string[]
        }>
    }
    matter_id?: string
    cases_used: number
    issues_addressed: number
    
    // Phase 2: Knowledge Base
    kb_insights?: KBInsights
    kb_available?: boolean
    similar_matters_count?: number
    
    // Phase 1: Full Judgments
    used_full_judgments?: boolean
    full_judgment_count?: number
    total_judgment_words?: number
    
    // Phase 3: Caching
    cache_statistics?: CacheStatistics
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

// ==========================================
// Cookie Authentication Types
// ==========================================

/**
 * Lexis cookie structure from browser export
 */
export interface LexisCookie {
    name: string
    value: string
    domain?: string
    path?: string
    httpOnly?: boolean
    secure?: boolean
    expirationDate?: number
}

/**
 * Cookie validation request payload
 */
export interface CookieValidationRequest {
    cookies: LexisCookie[]
}

/**
 * Cookie validation response
 */
export interface CookieValidationResponse {
    valid: boolean
    message: string
    estimated_expiry?: string
}

/**
 * Cookie save response
 */
export interface CookieSaveResponse {
    success: boolean
    message: string
    auth_method: 'um_library' | 'cookies'
    expires_at?: string
}

/**
 * Cookie status response (from /status endpoint)
 */
export interface CookieStatusResponse {
    auth_method: 'um_library' | 'cookies'
    has_cookies: boolean
    expires_at?: string
    is_expired?: boolean
    status: 'active' | 'expired' | 'using_default'
}

/**
 * User authentication method preference
 */
export type AuthMethod = 'um_library' | 'cookies'
