'use client';

import { Info } from 'lucide-react';
import type { ClinicalMapping } from '@/types';
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

export function ClinicalMappingCard({ mapping, onCorrect }: ClinicalMappingCardProps) {
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
      <CardContent className="space-y-4 text-sm">
        <p className="text-muted-foreground">
          Your query: <span className="text-foreground">{mapping.user_query}</span>
        </p>
        <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Mapping confidence</span>
          <span className="font-mono text-sm font-semibold">{Math.round(mapping.confidence * 100)}%</span>
        </div>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          <Field label="Procedure" value={mapping.procedure} />
          <Field label="Category" value={mapping.category} />
          <Field label="ICD-10" value={`${mapping.icd10_code} — ${mapping.icd10_label}`} />
          <Field label="SNOMED CT" value={mapping.snomed_code} />
        </div>

        <div className="rounded-lg border border-border bg-muted/30 p-3">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Typical pathway</p>
          <div className="grid gap-2">
            {mapping.pathway.map((step) => (
              <div key={step.step} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-background p-2">
                <p className="font-medium">
                  [{step.step}] {step.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {step.duration} · {formatCostRangeFull(step.cost_range)}
                </p>
              </div>
            ))}
          </div>
        </div>

        {mapping.confidence_factors && mapping.confidence_factors.length > 0 && (
          <div className="rounded-lg border border-border p-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Confidence drivers
            </p>
            <div className="space-y-2">
              {mapping.confidence_factors.map((factor) => (
                <div key={factor.key} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-foreground">{factor.label}</span>
                    <span className="font-mono text-muted-foreground">{factor.score}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted">
                    <div className="h-2 rounded-full bg-primary" style={{ width: `${factor.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Symptom-to-condition mapping is approximate. The same symptoms may indicate different conditions. This tool helps you research and prepare; your doctor makes the diagnosis.
        </p>

        <Button variant="link" className="h-auto p-0" onClick={onCorrect}>
          Correct this interpretation
        </Button>
      </CardContent>
    </Card>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
