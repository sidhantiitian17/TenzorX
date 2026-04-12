'use client';

import { motion } from 'framer-motion';
import type { CostBreakdown as CostBreakdownType } from '@/types';
import { formatCostRangeFull } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface CostBreakdownProps {
  breakdown: CostBreakdownType;
  showTable?: boolean;
}

const costComponents = [
  {
    key: 'procedure' as const,
    label: 'Procedure / Surgery',
    color: 'bg-[var(--c-cost-procedure)]',
    includes: 'Surgeon fee, OT charges, anesthesia, implants',
  },
  {
    key: 'doctor_fees' as const,
    label: 'Doctor Fees',
    color: 'bg-[var(--c-cost-doctor)]',
    includes: 'Consultation (pre-op + post-op), specialist review',
  },
  {
    key: 'hospital_stay' as const,
    label: 'Hospital Stay',
    color: 'bg-[var(--c-cost-stay)]',
    includes: 'Room charges per night multiplied by expected stay',
  },
  {
    key: 'diagnostics' as const,
    label: 'Diagnostics',
    color: 'bg-[var(--c-cost-diagnostics)]',
    includes: 'X-ray, MRI/CT, blood work, ECG',
  },
  {
    key: 'medicines' as const,
    label: 'Medicines',
    color: 'bg-[var(--c-cost-medicines)]',
    includes: 'Drugs, IV fluids, consumables',
  },
  {
    key: 'contingency' as const,
    label: 'Contingency',
    color: 'bg-[var(--c-cost-contingency)]',
    includes: 'ICU reserve, complication buffer, extended stay risk',
  },
];

export function CostBreakdown({ breakdown, showTable = true }: CostBreakdownProps) {
  const totalMax = Object.values(breakdown).reduce((sum, range) => sum + range.max, 0) || 1;

  return (
    <div className="space-y-3">
      <TooltipProvider>
        {costComponents.map((component, index) => {
          const range = breakdown[component.key];
          const widthPercent = Math.max(8, (range.max / totalMax) * 100);

          return (
            <Tooltip key={component.key}>
              <TooltipTrigger asChild>
                <div className="space-y-1 cursor-help">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <p className="font-medium">{component.label}</p>
                    <p className="font-mono text-xs text-muted-foreground">{formatCostRangeFull(range)}</p>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-muted">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${widthPercent}%` }}
                      transition={{ duration: 0.6, delay: index * 0.08 }}
                      className={cn('h-full rounded-full', component.color)}
                    />
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs text-sm">
                <p className="font-medium">{component.label}</p>
                <p className="text-muted-foreground">Includes: {component.includes}</p>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </TooltipProvider>

      {/* Summary table */}
      {showTable && (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50">
                <th className="text-left font-medium px-3 py-2">Component</th>
                <th className="text-right font-medium px-3 py-2">Min</th>
                <th className="text-right font-medium px-3 py-2">Max</th>
              </tr>
            </thead>
            <tbody>
              {costComponents.map((component, index) => {
                const range = breakdown[component.key];
                return (
                  <tr
                    key={component.key}
                    className={cn(
                      'border-t border-border',
                      index % 2 === 0 && 'bg-muted/20'
                    )}
                  >
                    <td className="px-3 py-2 flex items-center gap-2">
                      <div className={cn('w-2 h-2 rounded-sm', component.color)} />
                      {component.label}
                    </td>
                    <td className="text-right font-mono px-3 py-2">
                      {range.min.toLocaleString('en-IN')}
                    </td>
                    <td className="text-right font-mono px-3 py-2">
                      {range.max.toLocaleString('en-IN')}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
