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
    <div className="rounded-xl border border-border bg-card p-3">
      <p className="mb-2 text-sm font-semibold">Treatment Pathway</p>
      <div className="overflow-x-auto pb-1">
        <div className="flex min-w-max items-center gap-2">
          {pathway.map((step, index) => {
            const isActive = activeStep === step.step;
            return (
              <div key={step.step} className="flex items-center gap-2">
                <button
                  onClick={() => setActiveStep(step.step)}
                  className={
                    isActive
                      ? 'rounded-lg border border-primary bg-primary/10 px-3 py-2 text-left'
                      : 'rounded-lg border border-border bg-background px-3 py-2 text-left hover:border-primary/40'
                  }
                >
                  <p className="text-xs font-medium text-muted-foreground">Step {step.step}</p>
                  <p className="text-sm font-semibold text-foreground">{step.name}</p>
                  <p className="text-xs text-muted-foreground">{step.duration}</p>
                  <p className="text-xs font-mono text-muted-foreground">{formatCostRangeFull(step.cost_range)}</p>
                </button>
                {index < pathway.length - 1 && (
                  <span className="text-muted-foreground">-&gt;</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
