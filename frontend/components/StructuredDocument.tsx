
import React from 'react';
// Note: In a real environment we would install react-markdown
// For now we will use a simple parser or dangerousHTML if we trust the source,
// or simple text splitting. Ideally we use react-markdown.
// Assuming we don't have it installed yet, I'll build a lightweight formatter.

interface StructuredDocumentProps {
    content: string;
    sourceMap?: any[];
    isLoading?: boolean;
}

export default function StructuredDocument({ content, sourceMap, isLoading }: StructuredDocumentProps) {

    if (isLoading && !content) {
        return (
            <div className="w-full h-96 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-primary)] flex items-center justify-center animate-pulse">
                <div className="text-[var(--text-tertiary)] font-mono">Loading document preview...</div>
            </div>
        );
    }

    return (
        <div className="w-full bg-white rounded-xl shadow-xl overflow-hidden border border-gray-200">
            {/* Legal Paper Header */}
            <div className="h-2 bg-[var(--gold-primary)] w-full"></div>

            <div className="p-12 min-h-[800px] text-black font-serif relative">
                {/* Line Numbers Decoration (Left) */}
                <div className="absolute left-6 top-12 bottom-12 w-6 text-xs text-slate-300 font-mono text-right select-none space-y-6">
                    {Array.from({ length: 40 }).map((_, i) => (
                        <div key={i}>{(i + 1) * 5}</div>
                    ))}
                </div>

                {/* Content */}
                <div className="ml-8 prose prose-slate max-w-none">
                    <PaperContent text={content} />
                </div>
            </div>
        </div>
    );
}

// Simple formatter to handle basic newlines and headers if not using a full markdown library
function PaperContent({ text }: { text: string }) {
    if (!text) return null;

    // Split by double newlines for paragraphs
    const paragraphs = text.split('\n\n');

    return (
        <div className="space-y-6 leading-relaxed text-lg">
            {paragraphs.map((para, idx) => {
                // Simple header detection
                if (para.startsWith('# ')) {
                    return <h1 key={idx} className="text-2xl font-bold text-center uppercase tracking-wider mb-8">{para.replace('# ', '')}</h1>
                }
                if (para.toUpperCase() === para && para.length < 50) {
                    return <h2 key={idx} className="text-xl font-bold text-center mt-8 mb-4">{para}</h2>
                }
                if (para.includes('IN THE HIGH COURT') || para.includes('DALAM MAHKAMAH')) {
                    return <div key={idx} className="text-center font-bold whitespace-pre-wrap">{para}</div>
                }

                return <p key={idx} className="text-justify whitespace-pre-wrap">{para}</p>;
            })}
        </div>
    );
}
