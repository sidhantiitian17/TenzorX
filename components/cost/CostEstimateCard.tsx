'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Info, AlertTriangle } from 'lucide-react';
import type { CostEstimate } from '@/types';
import { formatCostRangeFull, formatINRFull } from '@/lib/formatters';
import { ConfidenceScore } from './ConfidenceScore';
import { CostBreakdown } from './CostBreakdown';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';

interface CostEstimateCardProps {
  estimate: CostEstimate;
  comorbidityWarnings?: string[];
}

export function CostEstimateCard({ estimate, comorbidityWarnings = [] }: CostEstimateCardProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showFactors, setShowFactors] = useState(false);

  const isLowConfidence = estimate.confidence < 0.4;

  const exportSummary = () => {
    const lines = [
      `Procedure: ${estimate.procedure}`,
      `ICD-10: ${estimate.icd10_code}`,
      `Location: ${estimate.location || 'India'}`,
      `Total range: ${formatCostRangeFull(estimate.cost_range)}`,
      estimate.typical_range ? `Typical range: ${formatCostRangeFull(estimate.typical_range)}` : '',
      `Confidence score: ${Math.round(estimate.confidence * 100)}%`,
      'Disclaimer: Decision support only. Consult a qualified doctor before making decisions.',
    ].filter(Boolean);
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'healthnav-estimate-summary.txt';
    link.click();
    URL.revokeObjectURL(url);
  };

  const shareSummary = async () => {
    const text = `HealthNav estimate for ${estimate.procedure}: ${formatCostRangeFull(estimate.cost_range)} (confidence ${Math.round(estimate.confidence * 100)}%).`;
    if (navigator.share) {
      await navigator.share({ title: 'HealthNav Estimate', text });
      return;
    }
    await navigator.clipboard.writeText(text);
  };

  return (
    <Card className="overflow-hidden">
      {/* Low confidence warning */}
      {isLowConfidence && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-800">
            Cost estimates for this procedure have high variability. The ranges shown are broad benchmarks only.
          </p>
        </div>
      )}

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-lg">Estimated Cost for {estimate.procedure}</CardTitle>
            <p className="text-sm text-muted-foreground mt-0.5">
              {estimate.location || 'India'} · {estimate.tier || 'mid'} tier hospitals
            </p>
          </div>
          <ConfidenceScore confidence={estimate.confidence} size="sm" />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Total cost range */}
        <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Total range</p>
          <p className="text-xl font-semibold font-mono text-foreground">{formatCostRangeFull(estimate.cost_range)}</p>
          {estimate.typical_range && (
            <p className="text-sm text-muted-foreground">
              Typical: {formatCostRangeFull(estimate.typical_range)}
            </p>
          )}
        </div>

        {estimate.tier_comparison && (
          <div className="rounded-lg border border-border p-3">
            <p className="mb-2 text-sm font-medium">Compare cost by hospital tier</p>
            <div className="grid gap-2 text-sm sm:grid-cols-3">
              <TierCell label="Budget" value={estimate.tier_comparison.budget} />
              <TierCell label="Mid-tier" value={estimate.tier_comparison.mid} featured />
              <TierCell label="Premium" value={estimate.tier_comparison.premium} />
            </div>
          </div>
        )}

        {estimate.confidence_factors && estimate.confidence_factors.length > 0 && (
          <div className="rounded-lg border border-border p-3">
            <p className="mb-2 text-sm font-medium">Confidence drivers</p>
            <div className="space-y-2">
              {estimate.confidence_factors.map((factor) => (
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

        {estimate.geo_adjustment && (
          <p className="text-xs text-muted-foreground">
            Cost adjusted for {estimate.geo_adjustment.city_name} ({estimate.geo_adjustment.city_tier}).
            Approximately {Math.round(estimate.geo_adjustment.discount_vs_metro * 100)}% lower than metro benchmarks for similar care pathways.
          </p>
        )}

        {/* Comorbidity warnings */}
        {comorbidityWarnings.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <div className="text-sm text-amber-800">
              {comorbidityWarnings.map((warning, index) => (
                <p key={index}>{warning}</p>
              ))}
            </div>
          </div>
        )}

        {/* Cost breakdown collapsible */}
        <Collapsible open={showBreakdown} onOpenChange={setShowBreakdown}>
          <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors">
            <span>View Cost Breakdown</span>
            <ChevronDown
              className={cn(
                'h-4 w-4 transition-transform',
                showBreakdown && 'rotate-180'
              )}
            />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <AnimatePresence>
              {showBreakdown && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="pt-2"
                >
                  <CostBreakdown breakdown={estimate.cost_breakdown} />
                </motion.div>
              )}
            </AnimatePresence>
          </CollapsibleContent>
        </Collapsible>

        {estimate.risk_adjustments && estimate.risk_adjustments.length > 0 && (
          <div className="rounded-lg border border-border p-3">
            <p className="mb-2 text-sm font-medium">Comorbidity-adjusted impact</p>
            <div className="space-y-1.5 text-sm text-muted-foreground">
              {estimate.risk_adjustments.map((risk) => (
                <p key={risk.factor}>
                  +{risk.factor}: {formatINRFull(risk.cost_delta_min)} to {formatINRFull(risk.cost_delta_max)}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* What affects this estimate? */}
        <Collapsible open={showFactors} onOpenChange={setShowFactors}>
          <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors">
            <span className="flex items-center gap-1.5">
              <Info className="h-4 w-4" />
              What may increase cost?
            </span>
            <ChevronDown
              className={cn(
                'h-4 w-4 transition-transform',
                showFactors && 'rotate-180'
              )}
            />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <AnimatePresence>
              {showFactors && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <div className="space-y-2 pt-2 text-sm text-muted-foreground">
                    <p>Extended ICU or HDU stay</p>
                    <p>Complications requiring additional procedures</p>
                    <p>Premium room upgrades</p>
                    <p>Geographic cost variation</p>
                    <p>Choice of implants or consumables</p>
                    <p>Pre-existing conditions (diabetes, hypertension)</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </CollapsibleContent>
        </Collapsible>

        <div className="flex flex-wrap gap-2 pt-1">
          <Button size="sm" variant="outline" onClick={exportSummary}>
            Export Estimate (TXT)
          </Button>
          <Button size="sm" variant="outline" onClick={shareSummary}>
            Share
          </Button>
          <Button size="sm" onClick={() => setShowBreakdown(true)}>
            View Breakdown
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function TierCell({
  label,
  value,
  featured = false,
}: {
  label: string;
  value: { min: number; max: number };
  featured?: boolean;
}) {
  return (
    <div
      className={cn(
        'rounded-md border px-3 py-2',
        featured ? 'border-primary bg-primary/5' : 'border-border bg-card'
      )}
    >
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-mono text-sm font-medium">{formatCostRangeFull(value)}</p>
    </div>
  );
}
