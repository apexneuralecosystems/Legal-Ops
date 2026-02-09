'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, Play, Scroll } from 'lucide-react';

export type WorkflowStep = {
    id: string;
    label: string;
    status: 'waiting' | 'active' | 'completed' | 'error';
    message?: string;
};

interface WorkflowProgressProps {
    steps: WorkflowStep[];
    overallStatus: 'idle' | 'running' | 'completed' | 'error';
}

export default function WorkflowProgress({ steps, overallStatus }: WorkflowProgressProps) {
    return (
        <div className="w-full p-8 bg-[#0F0F0F] border border-[#D4A853]/20 shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
            <div className="flex items-center justify-between mb-8 border-b border-[#D4A853]/10 pb-4">
                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[#D4A853] flex items-center gap-3">
                    {overallStatus === 'running' ? (
                        <div className="relative">
                            <div className="absolute inset-0 bg-[#D4A853] blur-md opacity-20 animate-pulse"></div>
                            <Loader2 className="w-4 h-4 animate-spin relative" />
                        </div>
                    ) : (
                        <Scroll className="w-4 h-4" />
                    )}
                    Synthesis State
                </h3>
                <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold tracking-widest px-2 py-0.5 border ${
                        overallStatus === 'running' ? 'border-[#D4A853] text-[#D4A853]' : 'border-gray-700 text-gray-500'
                    }`}>
                        {overallStatus.toUpperCase()}
                    </span>
                </div>
            </div>

            <div className="space-y-6 relative">
                {/* Connector Line - Thinner, more elegant */}
                <div className="absolute left-[11px] top-2 bottom-2 w-[1px] bg-gradient-to-b from-[#D4A853]/40 via-[#D4A853]/10 to-[#D4A853]/40" />

                <AnimatePresence>
                    {steps.map((step, index) => (
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -5 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-start gap-4 relative z-10"
                        >
                            {/* Step Indicator */}
                            <div className={`mt-1.5 w-[22px] h-[22px] flex items-center justify-center border transition-all duration-500 ${
                                    step.status === 'completed' 
                                    ? 'bg-[#D4A853] border-[#D4A853] shadow-[0_0_15px_rgba(212,168,83,0.3)]' :
                                    step.status === 'active' 
                                    ? 'bg-black border-[#D4A853] shadow-[0_0_10px_rgba(212,168,83,0.2)]' :
                                    step.status === 'error' 
                                    ? 'bg-red-950 border-red-500' :
                                    'bg-black border-gray-800'
                                }`}>
                                {step.status === 'completed' ? (
                                    <CheckCircle2 className="w-3 h-3 text-black" />
                                ) : step.status === 'active' ? (
                                    <div className="w-1.5 h-1.5 bg-[#D4A853] animate-pulse rounded-full" />
                                ) : (
                                    <div className="w-1 h-1 bg-gray-600 rounded-full" />
                                )}
                            </div>

                            {/* Step Content */}
                            <div className="flex-1">
                                <div className={`text-[13px] font-bold tracking-wide uppercase font-serif transition-colors duration-500 ${
                                        step.status === 'active' ? 'text-white' :
                                        step.status === 'completed' ? 'text-[#D4A853]/70' :
                                        'text-gray-600'
                                    }`}>
                                    {step.label}
                                </div>

                                {/* Active Message */}
                                <AnimatePresence mode="wait">
                                    {(step.status === 'active' || (step.status === 'completed' && step.message)) && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="text-[11px] font-serif italic mt-1.5 text-gray-400 border-l border-[#D4A853]/20 pl-3 leading-relaxed">
                                                {step.message || (step.status === 'active' ? 'Processing archival record...' : '')}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    );
}
