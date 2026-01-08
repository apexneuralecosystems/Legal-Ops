
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, Play } from 'lucide-react';

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
        <div className="w-full max-w-2xl mx-auto p-6 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-primary)] shadow-lg">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-[var(--gold-primary)] flex items-center gap-2">
                    {overallStatus === 'running' && <Loader2 className="w-5 h-5 animate-spin" />}
                    {overallStatus === 'completed' && <CheckCircle2 className="w-5 h-5" />}
                    Workflow Progress
                </h3>
                <div className="text-xs text-[var(--text-secondary)] font-mono">
                    {overallStatus.toUpperCase()}
                </div>
            </div>

            <div className="space-y-4 relative">
                {/* Connector Line */}
                <div className="absolute left-[19px] top-4 bottom-4 w-0.5 bg-[var(--border-secondary)] -z-10" />

                <AnimatePresence>
                    {steps.map((step, index) => (
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex items-start gap-4"
                        >
                            {/* Step Icon */}
                            <div className={`mt-1 bg-[var(--bg-secondary)] rounded-full p-1 border-2 transition-colors duration-300 ${step.status === 'completed' ? 'border-[var(--green-primary)] text-[var(--green-primary)]' :
                                    step.status === 'active' ? 'border-[var(--gold-primary)] text-[var(--gold-primary)]' :
                                        step.status === 'error' ? 'border-red-500 text-red-500' :
                                            'border-[var(--text-tertiary)] text-[var(--text-tertiary)]'
                                }`}>
                                {step.status === 'completed' ? <CheckCircle2 className="w-5 h-5" /> :
                                    step.status === 'active' ? <Loader2 className="w-5 h-5 animate-spin" /> :
                                        step.status === 'error' ? <Circle className="w-5 h-5" /> : // Could be an X
                                            <Circle className="w-5 h-5" />}
                            </div>

                            {/* Step Content */}
                            <div className="flex-1 pb-4">
                                <div className={`text-sm font-medium transition-colors ${step.status === 'active' ? 'text-[var(--text-primary)]' :
                                        step.status === 'completed' ? 'text-[var(--text-secondary)]' :
                                            'text-[var(--text-tertiary)]'
                                    }`}>
                                    {step.label}
                                </div>

                                {/* Active/Completed Message */}
                                <AnimatePresence>
                                    {(step.status === 'active' || step.message) && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="text-xs font-mono mt-1 text-[var(--gold-secondary)]"
                                        >
                                            {step.message || (step.status === 'active' ? 'Processing...' : '')}
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
