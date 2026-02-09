'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface StructuredDocumentProps {
    content: string;
    sourceMap?: any[];
    isLoading?: boolean;
}

export default function StructuredDocument({ content, sourceMap, isLoading }: StructuredDocumentProps) {

    if (isLoading && !content) {
        return (
            <div className="w-full h-[600px] bg-white/5 flex flex-col items-center justify-center p-12 border border-[#D4A853]/10">
                <div className="w-12 h-[1px] bg-[#D4A853] animate-grow-x mb-8"></div>
                <div className="text-[#D4A853] font-serif italic text-lg opacity-60 tracking-widest animate-pulse">Initializing Archival Preview...</div>
            </div>
        );
    }

    return (
        <div className="w-full bg-white shadow-[0_20px_60px_rgba(0,0,0,0.15)] relative group">
            {/* Archival Binding Decoration */}
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#F5F5F5] border-r border-gray-200"></div>
            <div className="absolute left-4 top-0 bottom-0 w-[0.5px] bg-gray-100"></div>

            {/* Header Accent */}
            <div className="h-[2px] bg-gradient-to-r from-transparent via-[#D4A853] to-transparent w-full opacity-60"></div>

            <div className="p-16 lg:p-24 min-h-[600px] text-black font-serif relative overflow-hidden">
                {/* Render the actual content */}
                <PaperContent text={content} />

                {/* Footer decoration */}
                <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
                    <div className="w-8 h-[0.5px] bg-[#D4A853]"></div>
                    <div className="text-[10px] font-bold tracking-[0.3em] text-[#D4A853] uppercase">Heritage Doc-ID: L-ARCH-2024</div>
                </div>
            </div>
        </div>
    );
}

function PaperContent({ text }: { text: string }) {
    if (!text) return null;

    const paragraphs = text.split('\n\n');

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-10 leading-[1.8] text-[1.15rem] text-slate-900"
        >
            {paragraphs.map((para, idx) => {
                // Main Header
                if (para.startsWith('# ')) {
                    return (
                        <div key={idx} className="mb-16 text-center space-y-4">
                            <h1 className="text-3xl font-black text-black uppercase tracking-[0.1em] border-b-[0.5px] border-black/10 pb-6 inline-block min-w-[300px]">
                                {para.replace('# ', '')}
                            </h1>
                            <div className="flex justify-center gap-1">
                                <span className="w-1 h-1 bg-[#D4A853] rounded-full"></span>
                                <span className="w-1 h-1 bg-[#D4A853] rounded-full"></span>
                                <span className="w-1 h-1 bg-[#D4A853] rounded-full"></span>
                            </div>
                        </div>
                    )
                }

                // Sub headers / Bold sections
                if (para.toUpperCase() === para && para.length < 100) {
                    return (
                        <h2 key={idx} className="text-xl font-black tracking-tight border-l-2 border-[#D4A853] pl-6 py-1 my-12 bg-gray-50/50">
                            {para}
                        </h2>
                    )
                }

                // Court identifiers
                if (para.includes('IN THE HIGH COURT') || para.includes('DALAM MAHKAMAH') || para.includes('PLAINTIFF') || para.includes('DEFENDANT')) {
                    return (
                        <div key={idx} className="text-center font-black tracking-wider text-xl uppercase italic border-y-[0.5px] border-black/05 py-8 my-10 bg-slate-50/30">
                            {para}
                        </div>
                    )
                }

                // Standard paragraph
                return (
                    <p key={idx} className="text-justify indent-12 decoration-slate-200 underline-offset-8">
                        {para}
                    </p>
                );
            })}
        </motion.div>
    );
}
