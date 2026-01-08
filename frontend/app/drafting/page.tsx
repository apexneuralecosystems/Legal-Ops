'use client'

import { useState, Suspense, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Scale, Loader2, CheckCircle2, AlertCircle, FileText, Sparkles, Zap, Check, BookOpen, PenTool } from 'lucide-react'
import { api } from '@/lib/api'
import Sidebar from '@/components/Sidebar'
import WorkflowProgress, { WorkflowStep } from '@/components/WorkflowProgress'
import StructuredDocument from '@/components/StructuredDocument'

function DraftingContent() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const [matterId, setMatterId] = useState<string | null>(searchParams.get('matterId') || searchParams.get('matter'))

    const [selectedTemplate, setSelectedTemplate] = useState('TPL-HighCourt-MS-v2')
    const [selectedIssues, setSelectedIssues] = useState<any[]>([])
    const [selectedPrayers, setSelectedPrayers] = useState<any[]>([])

    // Streaming state
    const [streamStatus, setStreamStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
    const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([
        { id: 'plan_issues', label: 'Plan Strategy', status: 'waiting' },
        { id: 'select_template', label: 'Select Template', status: 'waiting' },
        { id: 'draft_content', label: 'Draft Content', status: 'waiting' },
        { id: 'qa_check', label: 'Quality Check', status: 'waiting' },
    ]);
    const [generatedPleading, setGeneratedPleading] = useState<any>(null);

    const { data: matter } = useQuery({
        queryKey: ['matter', matterId],
        queryFn: () => matterId ? api.getMatter(matterId) : null,
        enabled: !!matterId,
    })

    // Update matterId if search params change
    useEffect(() => {
        const mid = searchParams.get('matterId') || searchParams.get('matter')
        if (mid) setMatterId(mid)
    }, [searchParams])

    const templates = [
        { id: 'TPL-HighCourt-MS-v2', name: 'High Court Statement of Claim (Malay)', language: 'ms', gradient: 'from-[var(--neon-orange)] to-[var(--neon-red)]' },
        { id: 'TPL-HighCourt-EN-v2', name: 'High Court Statement of Claim (English)', language: 'en', gradient: 'from-[var(--neon-cyan)] to-[var(--neon-blue)]' },
    ]

    const matterIssues = matter?.issues || []
    const displayIssues = matterIssues.length > 0 ? matterIssues.map((issue: any, idx: number) => ({
        id: issue.id || `ISS-${idx + 1}`,
        title: issue.text_en || issue.title || `[Issue ${idx + 1} - Please specify]`,
        legal_basis: issue.legal_basis || ['[Legal basis to be specified]']
    })) : [
        { id: 'ISS-01', title: '[Please specify the legal issue / Sila nyatakan isu undang-undang]', legal_basis: ['[Legal basis / Asas undang-undang]'] }
    ]

    const matterRemedies = matter?.requested_remedies || []
    const displayPrayers = matterRemedies.length > 0 ? matterRemedies.map((remedy: any) => ({
        text_en: remedy.text || remedy.text_en || '[Remedy description]',
        text_ms: remedy.text_ms || '[Deskripsi remedi]'
    })) : [
        { text_en: '[Judgment for RM ______]', text_ms: '[Penghakiman untuk RM ______]' },
        { text_en: '[Interest and costs]', text_ms: '[Faedah dan kos]' }
    ]

    const toggleIssue = (issue: any) => {
        if (selectedIssues.find(i => i.id === issue.id)) {
            setSelectedIssues(selectedIssues.filter(i => i.id !== issue.id))
        } else {
            setSelectedIssues([...selectedIssues, issue])
        }
    }

    const togglePrayer = (prayer: any) => {
        if (selectedPrayers.find(p => p.text_en === prayer.text_en)) {
            setSelectedPrayers(selectedPrayers.filter(p => p.text_en !== prayer.text_en))
        } else {
            setSelectedPrayers([...selectedPrayers, prayer])
        }
    }

    // Streaming function
    const startDraftingStream = async () => {
        if (!matterId) return;

        setStreamStatus('running');
        setGeneratedPleading(null);

        // Reset steps
        setWorkflowSteps(steps => steps.map(s => ({ ...s, status: 'waiting', message: undefined })));

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8091'}/api/matters/${matterId}/draft/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    template_id: selectedTemplate,
                    issues_selected: selectedIssues,
                    prayers_selected: selectedPrayers,
                })
            });

            // DEBUG: Check what we sent
            const token = localStorage.getItem('access_token');
            console.log("Drafting Stream - Token used:", token ? token.substring(0, 10) + "..." : "NULL");
            if (!token) {
                alert("You are not logged in. Please log in again.");
                router.push('/login');
                return;
            }

            if (response.status === 401) {
                console.error("401 Unauthorized - Token rejected by backend.");
                alert("Session expired or invalid. Please log in again.");
                // router.push('/login'); // Optional auto-redirect
            }

            if (!response.ok) throw new Error('Failed to start workflow');

            // Read stream with proper SSE buffering
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) return;

            let buffer = ''; // Buffer for incomplete data

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // Append new data to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages (ending with \n\n)
                const messages = buffer.split('\n\n');

                // Keep the last incomplete message in buffer
                buffer = messages.pop() || '';

                for (const message of messages) {
                    if (message.startsWith('data: ')) {
                        try {
                            const jsonStr = message.slice(6);
                            const data = JSON.parse(jsonStr);
                            handleStreamEvent(data);
                        } catch (e) {
                            console.error('Error parsing SSE:', e, 'Raw:', message.slice(0, 200));
                        }
                    }
                }
            }

            // Process any remaining buffered data
            if (buffer.startsWith('data: ')) {
                try {
                    const data = JSON.parse(buffer.slice(6));
                    handleStreamEvent(data);
                } catch (e) {
                    console.error('Error parsing final SSE:', e);
                }
            }
        } catch (error) {
            console.error('Stream error:', error);
            setStreamStatus('error');
        }
    };

    const handleStreamEvent = (event: any) => {
        // DEBUG: Log every event received
        console.log("Drafting Stream Event:", event);

        if (event.type === 'status') {
            // Optional: Show global status toast
        }
        else if (event.type === 'progress') {
            const stepIdRaw = event.step;
            // Map backend node names to frontend step IDs
            let stepId = 'draft_content'; // Default fallback

            if (stepIdRaw === 'plan_issues') stepId = 'plan_issues';
            else if (stepIdRaw === 'select_template') stepId = 'select_template';
            else if (stepIdRaw === 'draft_malay' || stepIdRaw === 'draft_english') stepId = 'draft_content';
            else if (stepIdRaw === 'qa_check') stepId = 'qa_check';

            setWorkflowSteps(prev => {
                const newSteps = [...prev];
                const stepIndex = newSteps.findIndex(s => s.id === stepId);

                if (stepIndex !== -1) {
                    // Mark previous as completed
                    for (let i = 0; i < stepIndex; i++) {
                        newSteps[i].status = 'completed';
                    }
                    // Set current as active
                    newSteps[stepIndex].status = 'active';
                    newSteps[stepIndex].message = event.message;
                }

                return newSteps;
            });
        }
        else if (event.type === 'result') {
            console.log("FINAL RESULT DATA:", JSON.stringify(event.data, null, 2));
            setGeneratedPleading(event.data);
            setStreamStatus('completed');
            setWorkflowSteps(prev => prev.map(s => ({ ...s, status: 'completed' })));
        }
        else if (event.type === 'error') {
            console.error("Workflow Error:", event.message);
            setStreamStatus('error');
        }
    };

    // Helper to extract pleading content with multiple fallback paths
    const getPleadingContent = (data: any): string => {
        if (!data) return '';

        // Log for debugging
        console.log("Extracting content from:", Object.keys(data || {}));

        // Try all possible paths
        const paths = [
            data?.pleading_ms?.pleading_ms_text,
            data?.pleading_en?.pleading_en_text,
            data?.workflow_result?.pleading_ms?.pleading_ms_text,
            data?.workflow_result?.pleading_en?.pleading_en_text,
            // Direct text fields
            data?.pleading_ms_text,
            data?.pleading_en_text,
            // If data itself is the text
            typeof data === 'string' ? data : null,
        ];

        for (const path of paths) {
            if (path && typeof path === 'string' && path.length > 0) {
                console.log("Found content at path, length:", path.length);
                return path;
            }
        }

        console.warn("No pleading content found in data structure");
        return '';
    };

    if (!matterId) {
        return (
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <div className="card p-12 text-center max-w-md">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--neon-orange)]/10 flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-[var(--neon-orange)]" />
                        </div>
                        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">No Matter Selected</h2>
                        <p className="text-[var(--text-secondary)] mb-6">Please select a matter from the dashboard to start drafting.</p>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-black hover:bg-gray-900 text-[var(--gold-primary)] font-bold rounded-lg transition-colors shadow-lg border-2 border-[var(--gold-primary)]"
                        >
                            <Sparkles className="w-5 h-5" />
                            Go to Dashboard
                        </button>
                    </div>
                </main>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            <Sidebar />
            <main className="flex-1 p-8 relative">
                <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--neon-pink)] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>
                <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-[var(--neon-purple)] opacity-5 blur-[100px] rounded-full pointer-events-none"></div>

                <div className="mb-10 animate-fade-in">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="w-12 h-12 rounded-lg bg-[var(--gold-primary)] flex items-center justify-center">
                            <Scale className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold text-black">Drafting Workflow</h1>
                            <p className="text-[var(--text-secondary)] mt-1">Generate bilingual legal pleadings with AI</p>
                        </div>
                    </div>
                    <div className="cyber-line mt-6"></div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
                    {/* Left Column: Configuration */}
                    <div className="lg:col-span-1 space-y-6">

                        {/* Progress Stepper */}
                        {streamStatus !== 'idle' && (
                            <WorkflowProgress steps={workflowSteps} overallStatus={streamStatus} />
                        )}

                        <div className="card p-6 animate-slide-up">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-[var(--neon-cyan)]" />
                                Template
                            </h2>
                            <div className="space-y-3">
                                {templates.map(template => (
                                    <button
                                        key={template.id}
                                        onClick={() => setSelectedTemplate(template.id)}
                                        className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-300 ${selectedTemplate === template.id
                                            ? 'border-[var(--neon-purple)] bg-[var(--neon-purple)]/5'
                                            : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${template.gradient} flex items-center justify-center`}>
                                                <FileText className="w-5 h-5 text-white" />
                                            </div>
                                            <div className="flex-1">
                                                <div className={`font-medium ${selectedTemplate === template.id ? 'text-[var(--neon-purple)]' : 'text-[var(--text-primary)]'}`}>
                                                    {template.name}
                                                </div>
                                                <div className="text-xs text-[var(--text-tertiary)]">
                                                    {template.language === 'ms' ? 'Bahasa Malaysia' : 'English'}
                                                </div>
                                            </div>
                                            {selectedTemplate === template.id && (
                                                <div className="w-3 h-3 bg-[var(--neon-green)] rounded-full"></div>
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="card p-6 animate-slide-up stagger-1">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-[var(--neon-orange)]" />
                                Issues ({selectedIssues.length})
                            </h2>
                            <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                                {displayIssues.map((issue: any) => (
                                    <label
                                        key={issue.id}
                                        className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${selectedIssues.find(i => i.id === issue.id)
                                            ? 'border-[var(--neon-orange)] bg-[var(--neon-orange)]/5'
                                            : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                            }`}
                                    >
                                        <div className="relative flex items-center mt-1">
                                            <input
                                                type="checkbox"
                                                checked={!!selectedIssues.find(i => i.id === issue.id)}
                                                onChange={() => toggleIssue(issue)}
                                                className="peer sr-only"
                                            />
                                            <div className="w-4 h-4 border-2 border-[var(--text-tertiary)] rounded flex items-center justify-center peer-checked:border-[var(--neon-orange)] peer-checked:bg-[var(--neon-orange)] transition-all">
                                                <Check className="w-3 h-3 text-white opacity-0 peer-checked:opacity-100" />
                                            </div>
                                        </div>
                                        <div className="font-medium text-sm text-[var(--text-primary)]">{issue.title}</div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="card p-6 animate-slide-up stagger-2">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-[var(--neon-pink)]" />
                                Prayers ({selectedPrayers.length})
                            </h2>
                            <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                                {displayPrayers.map((prayer: any, idx: number) => (
                                    <label
                                        key={idx}
                                        className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${selectedPrayers.find(p => p.text_en === prayer.text_en)
                                            ? 'border-[var(--neon-pink)] bg-[var(--neon-pink)]/5'
                                            : 'border-[var(--border-primary)] hover:border-[var(--border-secondary)] bg-[var(--bg-tertiary)]'
                                            }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={!!selectedPrayers.find(p => p.text_en === prayer.text_en)}
                                            onChange={() => togglePrayer(prayer)}
                                            className="mt-1 accent-[var(--neon-pink)]"
                                        />
                                        <div className="text-sm text-[var(--text-primary)]">{prayer.text_en}</div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={startDraftingStream}
                            disabled={selectedIssues.length === 0 || streamStatus === 'running'}
                            className={`w-full btn-primary py-4 flex items-center justify-center gap-2 animate-slide-up stagger-3 ${(selectedIssues.length === 0 || streamStatus === 'running') ? 'opacity-50 cursor-not-allowed' : ''
                                }`}
                        >
                            {streamStatus === 'running' ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Drafting...
                                </>
                            ) : (
                                <>
                                    <Scale className="w-5 h-5" />
                                    Generate Pleading
                                </>
                            )}
                        </button>
                    </div>

                    {/* Right Column: Preview */}
                    <div className="lg:col-span-2">
                        <div className="card p-6 h-full animate-slide-up stagger-2 flex flex-col">
                            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2 justify-between">
                                <div className="flex items-center gap-2">
                                    <BookOpen className="w-5 h-5 text-[var(--neon-purple)]" />
                                    Draft Preview
                                </div>
                                {generatedPleading && (
                                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 text-green-500 text-xs font-medium border border-green-500/20">
                                        <CheckCircle2 className="w-3 h-3" />
                                        Completed
                                    </div>
                                )}
                            </h2>

                            <div className="flex-1 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-primary)] overflow-hidden relative">
                                {generatedPleading ? (
                                    <div className="absolute inset-0 overflow-y-auto custom-scrollbar bg-white p-8">
                                        <StructuredDocument
                                            content={getPleadingContent(generatedPleading)}
                                        />
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-[var(--text-tertiary)] space-y-4">
                                        <div className="w-20 h-20 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center border border-[var(--border-primary)]">
                                            <PenTool className="w-10 h-10 opacity-50" />
                                        </div>
                                        <div className="text-center">
                                            <p className="font-medium text-lg">Ready to Draft</p>
                                            <p className="text-sm opacity-60 max-w-xs mx-auto mt-2">
                                                Select a template, legal issues, and desired remedies to generate your pleading.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default function DraftingPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen bg-[var(--bg-primary)]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-[var(--neon-cyan)]" />
                </main>
            </div>
        }>
            <DraftingContent />
        </Suspense>
    )
}
