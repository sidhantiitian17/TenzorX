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
    <Card className="overflow-hidden border-slate-700 bg-slate-800/30">
      {/* Low confidence warning */}
      {isLowConfidence && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-300">
            Cost estimates for this procedure have high variability. The ranges shown are broad benchmarks only.
          </p>
        </div>
      )}

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-lg text-slate-100">Estimated Cost for {estimate.procedure}</CardTitle>
            <p className="text-sm text-slate-400 mt-0.5">
              {estimate.location || 'India'} · {estimate.tier || 'mid'} tier hospitals
            </p>
          </div>
          <ConfidenceScore confidence={estimate.confidence} size="sm" />
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Total cost range */}
        <div className="space-y-2 rounded-lg border border-slate-700 bg-slate-900/50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Total Range</p>
          <p className="text-2xl font-semibold font-mono text-slate-100">{formatCostRangeFull(estimate.cost_range)}</p>
          {estimate.typical_range && (
            <p className="text-sm text-slate-400">
              Typical: {formatCostRangeFull(estimate.typical_range)}
            </p>
          )}
        </div>

        {estimate.tier_comparison && (
          <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-4">
            <p className="mb-3 text-sm font-medium text-slate-100">Compare cost by hospital tier</p>
            <div className="grid gap-3 text-sm sm:grid-cols-3">
              <TierCell label="Budget" value={estimate.tier_comparison.budget} />
              <TierCell label="Mid-tier" value={estimate.tier_comparison.mid} featured />
              <TierCell label="Premium" value={estimate.tier_comparison.premium} />
            </div>
          </div>
        )}

        {estimate.confidence_factors && estimate.confidence_factors.length > 0 && (
          <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-4">
            <p className="mb-3 text-sm font-medium text-slate-100">Confidence drivers</p>
            <div className="space-y-3">
              {estimate.confidence_factors.map((factor) => (
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

        {estimate.geo_adjustment && (
          <p className="text-xs text-slate-400">
            Cost adjusted for {estimate.geo_adjustment.city_name} ({estimate.geo_adjustment.city_tier}).
            Approximately {Math.round(estimate.geo_adjustment.discount_vs_metro * 100)}% lower than metro benchmarks for similar care pathways.
          </p>
        )}

        {/* Comorbidity warnings */}
        {comorbidityWarnings.length > 0 && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
            <div className="text-sm text-amber-300">
              {comorbidityWarnings.map((warning, index) => (
                <p key={index}>{warning}</p>
              ))}
            </div>
          </div>
        )}

        {/* Cost breakdown collapsible */}
        <Collapsible open={showBreakdown} onOpenChange={setShowBreakdown}>
          <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium text-slate-300 hover:text-slate-100 transition-colors">
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
          <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-4">
            <p className="mb-2 text-sm font-medium text-slate-100">Comorbidity-adjusted impact</p>
            <div className="space-y-1.5 text-sm text-slate-400">
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
          <CollapsibleTrigger className="flex items-center justify-between w-full py-2 text-sm font-medium text-slate-300 hover:text-slate-100 transition-colors">
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
                  <div className="space-y-2 pt-2 text-sm text-slate-400">
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
          <Button size="sm" variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700" onClick={exportSummary}>
            Export Estimate (TXT)
          </Button>
          <Button size="sm" variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700" onClick={shareSummary}>
            Share
          </Button>
          <Button size="sm" className="bg-teal-500 hover:bg-teal-600 text-white" onClick={() => setShowBreakdown(true)}>
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
        'rounded-lg border px-3 py-3',
        featured ? 'border-teal-500 bg-teal-500/10' : 'border-slate-700 bg-slate-900/50'
      )}
    >
      <p className={cn('text-xs uppercase tracking-wide', featured ? 'text-teal-400' : 'text-slate-400')}>{label}</p>
      <p className={cn('mt-1 font-mono text-sm font-medium', featured ? 'text-teal-100' : 'text-slate-300')}>{formatCostRangeFull(value)}</p>
    </div>
  );
}
