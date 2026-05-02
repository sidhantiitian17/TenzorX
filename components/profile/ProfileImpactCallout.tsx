'use client';

import type { RiskAdjustment } from '@/types';
import { formatINRShort } from '@/lib/formatters';

interface ProfileImpactCalloutProps {
  adjustments: RiskAdjustment[];
}

export function ProfileImpactCallout({ adjustments }: ProfileImpactCalloutProps) {
  if (adjustments.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-100 p-4">
      <p className="text-sm font-semibold text-slate-900">Your profile affects these estimates</p>
      <ul className="mt-2 space-y-1 text-sm text-slate-700">
        {adjustments.map((item) => (
          <li key={item.factor}>
            <span className="font-medium text-slate-900">{item.factor}</span>
            {' -> '} {item.impact} (+{formatINRShort(item.cost_delta_min)} to {formatINRShort(item.cost_delta_max)})
          </li>
        ))}
      </ul>
    </div>
  );
}
