'use client'

import { useState, Suspense, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { 
    Scale, 
    Loader2, 
    CheckCircle2, 
    AlertCircle, 
    FileText, 
    Sparkles, 
    Zap, 
    Check, 
    BookOpen, 
    PenTool,
    ChevronRight,
    Search,
    Gavel,
    ScrollText
} from 'lucide-react'
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
        { id: 'plan_issues', label: 'Strategic Planning', status: 'waiting' },
        { id: 'select_template', label: 'Template Selection', status: 'waiting' },
        { id: 'draft_content', label: 'Archival Synthesis', status: 'waiting' },
        { id: 'qa_check', label: 'Verification', status: 'waiting' },
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
        { id: 'TPL-HighCourt-MS-v2', name: 'High Court Statement of Claim', langName: 'Bahasa Malaysia', language: 'ms' },
        { id: 'TPL-HighCourt-EN-v2', name: 'High Court Statement of Claim', langName: 'English', language: 'en' },
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

            if (!response.ok) throw new Error('Failed to start workflow');

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            if (!reader) return;

            let buffer = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const messages = buffer.split('\n\n');
                buffer = messages.pop() || '';
                for (const message of messages) {
                    if (message.startsWith('data: ')) {
                        try {
                            const jsonStr = message.slice(6);
                            const data = JSON.parse(jsonStr);
                            handleStreamEvent(data);
                        } catch (e) {
                            console.error('Error parsing SSE:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Stream error:', error);
            setStreamStatus('error');
        }
    };

    const handleStreamEvent = (event: any) => {
        if (event.type === 'progress') {
            const stepIdRaw = event.step;
            let stepId = 'draft_content';
            if (stepIdRaw === 'plan_issues') stepId = 'plan_issues';
            else if (stepIdRaw === 'select_template') stepId = 'select_template';
            else if (stepIdRaw === 'draft_malay' || stepIdRaw === 'draft_english') stepId = 'draft_content';
            else if (stepIdRaw === 'qa_check') stepId = 'qa_check';

            setWorkflowSteps(prev => {
                const newSteps = [...prev];
                const stepIndex = newSteps.findIndex(s => s.id === stepId);
                if (stepIndex !== -1) {
                    for (let i = 0; i < stepIndex; i++) newSteps[i].status = 'completed';
                    newSteps[stepIndex].status = 'active';
                    newSteps[stepIndex].message = event.message;
                }
                return newSteps;
            });
        }
        else if (event.type === 'result') {
            setGeneratedPleading(event.data);
            setStreamStatus('completed');
            setWorkflowSteps(prev => prev.map(s => ({ ...s, status: 'completed' })));
        }
        else if (event.type === 'error') {
            setStreamStatus('error');
        }
    };

    const getPleadingContent = (data: any): string => {
        if (!data) return '';
        const paths = [
            data?.pleading_ms?.pleading_ms_text,
            data?.pleading_en?.pleading_en_text,
            data?.workflow_result?.pleading_ms?.pleading_ms_text,
            data?.workflow_result?.pleading_en?.pleading_en_text,
            data?.pleading_ms_text,
            data?.pleading_en_text,
            typeof data === 'string' ? data : null,
        ];
        for (const path of paths) {
            if (path && typeof path === 'string' && path.length > 0) return path;
        }
        return `[ARCHIVE ERROR] No content found. Available keys: ${Object.keys(data).join(', ')}`;
    };

    if (!matterId) {
        return (
            <div className="flex min-h-screen bg-[#0A0A0A] font-serif">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-[url('/grain.png')] opacity-[0.03] pointer-events-none"></div>
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="max-w-md w-full bg-[#1A1A1A] border border-[#D4A853]/20 p-12 text-center"
                    >
                        <AlertCircle className="w-12 h-12 text-[#D4A853] mx-auto mb-6" />
                        <h2 className="text-2xl font-bold text-white mb-4 tracking-tight font-serif uppercase">Registry Access Required</h2>
                        <p className="text-gray-400 mb-8 leading-relaxed">Please select a matter from the Executive Dashboard to proceed with the drafting workflow.</p>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-[#D4A853] hover:bg-[#B88A3E] text-white font-bold transition-all duration-300 shadow-xl"
                        >
                            <Gavel className="w-5 h-5" />
                            Return to Registry
                        </button>
                    </motion.div>
                </main>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen bg-[#0A0A0A] text-white selection:bg-[#D4A853]/30">
            <Sidebar />
            <main className="flex-1 p-8 relative overflow-hidden">
                {/* Archival Background Elements */}
                <div className="absolute inset-0 bg-[url('/grain.png')] opacity-[0.03] pointer-events-none"></div>
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#D4A853] opacity-[0.02] blur-[150px] rounded-full pointer-events-none"></div>
                
                <header className="mb-12 relative z-10">
                    <div className="flex items-center gap-6">
                        <div className="w-16 h-16 bg-[#1A1A1A] border border-[#D4A853]/40 flex items-center justify-center shadow-2xl">
                            <ScrollText className="w-8 h-8 text-[#D4A853]" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3 text-[#D4A853] text-xs font-bold tracking-[0.3em] uppercase mb-1">
                                <span className="w-8 h-[1px] bg-[#D4A853]"></span>
                                Automated Legal Drafting
                                <span className="w-8 h-[1px] bg-[#D4A853]"></span>
                            </div>
                            <h1 className="text-5xl font-black text-white tracking-tighter uppercase font-serif italic">
                                Drafting <span className="text-[#D4A853] not-italic">Chambers</span>
                            </h1>
                        </div>
                    </div>
                </header>

                <div className="grid lg:grid-cols-12 gap-10 max-w-7xl mx-auto items-start">
                    {/* Left Panel: Archives & Selections */}
                    <div className="lg:col-span-4 space-y-8">
                        
                        {/* Status Hub */}
                        <AnimatePresence>
                            {streamStatus !== 'idle' && (
                                <motion.div 
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    className="bg-[#141414] border border-[#D4A853]/20 overflow-hidden"
                                >
                                    <WorkflowProgress steps={workflowSteps} overallStatus={streamStatus} />
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Template Selection */}
                        <section className="bg-[#141414] border border-[#D4A853]/10 p-6 flex flex-col gap-6 shadow-2xl">
                            <div className="flex items-center justify-between border-b border-[#D4A853]/20 pb-4">
                                <h2 className="text-sm font-black uppercase tracking-widest text-[#D4A853] flex items-center gap-2">
                                    <FileText className="w-4 h-4" />
                                    Protocol Selection
                                </h2>
                            </div>
                            <div className="grid gap-4">
                                {templates.map(template => (
                                    <button
                                        key={template.id}
                                        onClick={() => setSelectedTemplate(template.id)}
                                        className={`group relative text-left p-5 transition-all duration-300 border ${
                                            selectedTemplate === template.id 
                                            ? 'bg-[#1A1A1A] border-[#D4A853] shadow-[0_0_20px_rgba(212,168,83,0.1)]' 
                                            : 'bg-transparent border-[#D4A853]/10 hover:border-[#D4A853]/40'
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="space-y-1">
                                                <div className={`text-xs font-bold tracking-widest uppercase ${selectedTemplate === template.id ? 'text-[#D4A853]' : 'text-gray-500Group-hover:text-gray-300'}`}>
                                                    {template.langName}
                                                </div>
                                                <div className="text-lg font-serif font-bold text-white leading-tight">
                                                    {template.name}
                                                </div>
                                            </div>
                                            {selectedTemplate === template.id && (
                                                <CheckCircle2 className="w-5 h-5 text-[#D4A853]" />
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </section>

                        {/* Legal Issues Archive */}
                        <section className="bg-[#141414] border border-[#D4A853]/10 p-6 shadow-2xl">
                             <div className="flex items-center justify-between border-b border-[#D4A853]/20 pb-4 mb-6">
                                <h2 className="text-sm font-black uppercase tracking-widest text-[#D4A853] flex items-center gap-2">
                                    <Zap className="w-4 h-4" />
                                    Legal Merits Archive
                                </h2>
                                <span className="bg-[#D4A853]/10 text-[#D4A853] px-2 py-0.5 text-[10px] font-bold border border-[#D4A853]/30">
                                    {selectedIssues.length} SELECTED
                                </span>
                            </div>
                            <div className="space-y-3 max-h-56 overflow-y-auto pr-2 custom-scrollbar">
                                {displayIssues.map((issue: any) => (
                                    <button
                                        key={issue.id}
                                        onClick={() => toggleIssue(issue)}
                                        className={`w-full text-left p-4 transition-all border ${
                                            selectedIssues.find(i => i.id === issue.id)
                                            ? 'bg-[#1A1A1A] border-[#D4A853]'
                                            : 'bg-transparent border-[#D4A853]/05 hover:border-[#D4A853]/20 hover:bg-slate-900/05'
                                        }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={`mt-1 w-4 h-4 border flex items-center justify-center transition-colors ${
                                                selectedIssues.find(i => i.id === issue.id) ? 'bg-[#D4A853] border-[#D4A853]' : 'border-[#D4A853]/40'
                                            }`}>
                                                {selectedIssues.find(i => i.id === issue.id) && <Check className="w-3 h-3 text-white" />}
                                            </div>
                                            <div className={`text-sm leading-relaxed ${selectedIssues.find(i => i.id === issue.id) ? 'text-white font-medium' : 'text-gray-400 group-hover:text-gray-200'}`}>
                                                {issue.title}
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </section>

                        {/* Prayers & Remedies */}
                        <section className="bg-[#141414] border border-[#D4A853]/10 p-6 shadow-2xl">
                             <div className="flex items-center justify-between border-b border-[#D4A853]/20 pb-4 mb-6">
                                <h2 className="text-sm font-black uppercase tracking-widest text-[#D4A853] flex items-center gap-2">
                                    <Sparkles className="w-4 h-4" />
                                    Prayer Registry
                                </h2>
                             </div>
                             <div className="space-y-3 max-h-56 overflow-y-auto pr-2 custom-scrollbar">
                                {displayPrayers.map((prayer: any, idx: number) => (
                                    <button
                                        key={idx}
                                        onClick={() => togglePrayer(prayer)}
                                        className={`w-full text-left p-4 transition-all border ${
                                            selectedPrayers.find(p => p.text_en === prayer.text_en)
                                            ? 'bg-[#1A1A1A] border-[#D4A853]'
                                            : 'bg-transparent border-[#D4A853]/05 hover:border-[#D4A853]/20 hover:bg-slate-900/05'
                                        }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={`mt-1 w-4 h-4 border flex items-center justify-center transition-colors ${
                                                selectedPrayers.find(p => p.text_en === prayer.text_en) ? 'bg-[#D4A853] border-[#D4A853]' : 'border-[#D4A853]/40'
                                            }`}>
                                                {selectedPrayers.find(p => p.text_en === prayer.text_en) && <Check className="w-3 h-3 text-white" />}
                                            </div>
                                            <div className={`text-sm ${selectedPrayers.find(p => p.text_en === prayer.text_en) ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>
                                                {prayer.text_en}
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </section>

                        {/* Executive Action */}
                        <button
                            onClick={startDraftingStream}
                            disabled={selectedIssues.length === 0 || streamStatus === 'running'}
                            className={`group relative w-full overflow-hidden p-5 bg-[#D4A853] text-white font-black uppercase tracking-widest transition-all duration-500 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#B88A3E] ${
                                streamStatus === 'running' ? 'animate-pulse' : ''
                            }`}
                        >
                            <div className="relative z-10 flex items-center justify-center gap-3">
                                {streamStatus === 'running' ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        <span>Synthesis in Progress...</span>
                                    </>
                                ) : (
                                    <>
                                        <Gavel className="w-5 h-5" />
                                        <span>Authorize Generation</span>
                                    </>
                                )}
                            </div>
                        </button>
                    </div>

                    {/* Right Panel: The Manuscript */}
                    <div className="lg:col-span-8 flex flex-col gap-6">
                        <section className="bg-[#141414] border border-[#D4A853]/20 p-8 h-full min-h-[800px] flex flex-col relative shadow-2xl">
                             <div className="flex items-center justify-between border-b border-[#D4A853]/30 pb-6 mb-8">
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 bg-black border border-[#D4A853]/40 flex items-center justify-center">
                                        <BookOpen className="w-5 h-5 text-[#D4A853]" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold font-serif text-white tracking-tight uppercase">Bilingual Manuscript</h2>
                                        <div className="flex items-center gap-2 text-[10px] text-[#D4A853] font-bold tracking-widest mt-1 uppercase">
                                            <span className="w-2 h-2 bg-[#D4A853] animate-pulse"></span>
                                            High Fidelity Drafting Output
                                        </div>
                                    </div>
                                </div>
                                
                                {generatedPleading && (
                                    <motion.div 
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="flex items-center gap-2 px-4 py-2 border border-[#D4A853]/30 bg-[#D4A853]/5 text-[#D4A853] text-xs font-black tracking-widest uppercase"
                                    >
                                        <CheckCircle2 className="w-4 h-4" />
                                        Verified Output
                                    </motion.div>
                                )}
                             </div>

                             <div className="flex-1 rounded-xl border border-[#D4A853]/05 bg-black/40 overflow-hidden relative">
                                {generatedPleading ? (
                                    <motion.div 
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        key={generatedPleading.id || 'result'}
                                        className="h-full"
                                    >
                                        <div className="absolute inset-0 overflow-y-auto custom-scrollbar p-10 bg-slate-900">
                                            <StructuredDocument
                                                content={getPleadingContent(generatedPleading)}
                                            />
                                        </div>
                                    </motion.div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-center space-y-8 p-12">
                                        <div className="relative">
                                            <div className="absolute inset-0 bg-[#D4A853]/20 blur-3xl rounded-full"></div>
                                            <div className="relative w-32 h-32 bg-[#0A0A0A] border-[0.5px] border-[#D4A853]/30 flex items-center justify-center shadow-inner">
                                                <PenTool className="w-12 h-12 text-[#D4A853]/40" />
                                            </div>
                                        </div>
                                        <div className="max-w-md">
                                            <h3 className="text-2xl font-bold font-serif text-white mb-4 uppercase tracking-tighter">Awaiting Authorization</h3>
                                            <p className="text-gray-500 leading-relaxed font-serif italic text-lg opacity-80">
                                                Select the case merits and drafting protocol from the sidebar to initialize the archival synthesis engine.
                                            </p>
                                        </div>
                                        <div className="flex gap-4 opacity-30 grayscale pointer-events-none">
                                            <div className="h-[1px] w-20 bg-[#D4A853]"></div>
                                            <div className="h-[1px] w-4 bg-[#D4A853]"></div>
                                            <div className="h-[1px] w-20 bg-[#D4A853]"></div>
                                        </div>
                                    </div>
                                )}
                             </div>
                        </section>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default function DraftingPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen bg-[#0A0A0A]">
                <Sidebar />
                <main className="flex-1 p-8 flex items-center justify-center">
                    <Loader2 className="w-12 h-12 animate-spin text-[#D4A853]" />
                </main>
            </div>
        }>
            <DraftingContent />
        </Suspense>
    )
}
