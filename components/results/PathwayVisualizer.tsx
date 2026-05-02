'use client';

import { useState } from 'react';
import type { PathwayStep } from '@/types';
import { formatCostRangeFull } from '@/lib/formatters';

interface PathwayVisualizerProps {
  pathway: PathwayStep[];
}

export function PathwayVisualizer({ pathway }: PathwayVisualizerProps) {
  const [activeStep, setActiveStep] = useState(pathway[0]?.step ?? 1);

  if (pathway.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/30 p-4">
      <p className="mb-4 text-sm font-semibold text-slate-100">Treatment Pathway</p>
      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-max items-stretch gap-3">
          {pathway.map((step, index) => {
            const isActive = activeStep === step.step;
            return (
              <div key={step.step} className="flex items-center gap-3">
                <button
                  onClick={() => setActiveStep(step.step)}
                  className={
                    isActive
                      ? 'rounded-lg border border-teal-500 bg-teal-500/10 px-4 py-3 text-left min-w-36'
                      : 'rounded-lg border border-slate-700 bg-slate-900/50 px-4 py-3 text-left min-w-36 hover:border-slate-600'
                  }
                >
                  <p className="text-[10px] font-medium text-slate-400 mb-1">Step {step.step}</p>
                  <p className="text-sm font-semibold text-slate-100">{step.name}</p>
                  <p className="text-xs text-slate-400 mt-1">{step.duration}</p>
                  <p className="text-xs font-mono text-slate-400 mt-1">{formatCostRangeFull(step.cost_range)}</p>
                </button>
                {index < pathway.length - 1 && (
                  <span className="text-slate-500 text-lg">-&gt;</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
