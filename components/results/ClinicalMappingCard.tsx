'use client';

import { useState } from 'react';
import { Info, ChevronDown, ChevronUp } from 'lucide-react';
import type { ClinicalMapping, ClinicalPhaseDetail } from '@/types';
import { formatCostRangeFull } from '@/lib/formatters';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ClinicalMappingCardProps {
  mapping: ClinicalMapping;
  onCorrect: () => void;
}

const phaseIcons: Record<ClinicalPhaseDetail['phase'], string> = {
  consultation: '🩺',
  diagnostics: '🔬',
  procedure: '🏥',
  observation_stay: '🛏️',
  follow_up_medication: '💊',
};

const phaseColors: Record<ClinicalPhaseDetail['phase'], string> = {
  consultation: 'bg-blue-500/10 border-blue-500/20 hover:bg-blue-500/20',
  diagnostics: 'bg-purple-500/10 border-purple-500/20 hover:bg-purple-500/20',
  procedure: 'bg-red-500/10 border-red-500/20 hover:bg-red-500/20',
  observation_stay: 'bg-orange-500/10 border-orange-500/20 hover:bg-orange-500/20',
  follow_up_medication: 'bg-green-500/10 border-green-500/20 hover:bg-green-500/20',
};

export function ClinicalMappingCard({ mapping, onCorrect }: ClinicalMappingCardProps) {
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  const togglePhase = (phase: string) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(phase)) {
      newExpanded.delete(phase);
    } else {
      newExpanded.add(phase);
    }
    setExpandedPhases(newExpanded);
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base">Clinical Interpretation</CardTitle>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button aria-label="How mapping works" className="text-muted-foreground hover:text-foreground">
                  <Info className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs text-sm">
                We map natural language to ICD-10 and SNOMED CT to improve provider matching and cost benchmark accuracy.
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>
      <CardContent className="space-y-5 text-sm">
        <div className="text-slate-300">
          Your query: <span className="text-slate-100 font-medium">{mapping.user_query}</span>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-400">Mapping Confidence</span>
          <span className="font-mono text-lg font-semibold text-slate-100">{Math.round(mapping.confidence * 100)}%</span>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="Procedure" value={mapping.procedure} />
          <Field label="Category" value={mapping.category} />
          <Field label="ICD-10" value={`${mapping.icd10_code} — ${mapping.icd10_label}`} />
          <Field label="SNOMED CT" value={mapping.snomed_code} />
        </div>

        {/* Clinical Phases Breakdown */}
        {mapping.clinical_phases && mapping.clinical_phases.length > 0 && (
          <div className="rounded-lg border border-border bg-muted/30 p-3">
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Treatment Pathway - 5 Clinical Phases
            </p>
            <div className="space-y-2">
              {mapping.clinical_phases.map((phase, index) => (
                <div
                  key={phase.phase}
                  className={`rounded-lg border ${phaseColors[phase.phase]} overflow-hidden`}
                >
                  <button
                    onClick={() => togglePhase(phase.phase)}
                    className="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-white/50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{phaseIcons[phase.phase]}</span>
                      <div>
                        <p className="font-medium text-foreground text-sm">{phase.name}</p>
                        <p className="text-xs text-muted-foreground">{phase.duration}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-muted-foreground">
                        {formatCostRangeFull({ min: phase.cost_min, max: phase.cost_max })}
                      </span>
                      {expandedPhases.has(phase.phase) ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </button>
                  
                  {expandedPhases.has(phase.phase) && (
                    <div className="px-3 pb-3 pt-2 border-t border-border/50">
                      <p className="text-xs text-muted-foreground mb-2">{phase.description}</p>
                      
                      <div className="mb-2">
                        <p className="text-xs font-medium text-foreground mb-1">AI Explanation:</p>
                        <p className="text-xs text-muted-foreground italic">{phase.llm_explanation}</p>
                      </div>
                      
                      <div className="mb-2">
                        <p className="text-xs font-medium text-foreground mb-1">Activities:</p>
                        <ul className="text-xs text-muted-foreground list-disc list-inside space-y-0.5">
                          {phase.activities.map((activity, i) => (
                            <li key={i}>{activity}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Responsible: {phase.responsible_party}</span>
                        <span className="font-mono text-muted-foreground">
                          {formatCostRangeFull({ min: phase.cost_min, max: phase.cost_max })}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Typical pathway display */}
        {mapping.pathway && mapping.pathway.length > 0 && (
          <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-slate-400">Typical Pathway</p>
            <div className="space-y-2">
              {mapping.pathway.map((step) => (
                <div key={step.step} className="flex items-center justify-between gap-4 rounded-md bg-slate-900/50 px-4 py-3">
                  <p className="font-medium text-slate-100">
                    [{step.step}] {step.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {step.duration} · {formatCostRangeFull(step.cost_range)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {mapping.confidence_factors && mapping.confidence_factors.length > 0 && (
          <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-slate-400">
              Confidence drivers
            </p>
            <div className="space-y-3">
              {mapping.confidence_factors.map((factor) => (
                <div key={factor.key} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">{factor.label}</span>
                    <span className="font-mono text-slate-400">{factor.score}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-700">
                    <div className="h-2 rounded-full bg-teal-500" style={{ width: `${factor.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="rounded-lg border border-slate-700 bg-slate-800/30 px-4 py-3 text-xs text-slate-400">
          Symptom-to-condition mapping is approximate. The same symptoms may indicate different conditions. This tool helps you research and prepare; your doctor makes the diagnosis.
        </p>

        <Button variant="link" className="h-auto p-0 text-teal-400 hover:text-teal-300" onClick={onCorrect}>
          Correct this interpretation
        </Button>
      </CardContent>
    </Card>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/30 px-4 py-3">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className="font-medium text-slate-100">{value}</p>
    </div>
  );
}
