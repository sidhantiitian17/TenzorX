'use client';

import type { RiskAdjustment } from '@/types';
import { formatINRShort } from '@/lib/formatters';

interface ProfileImpactCalloutProps {
  adjustments: RiskAdjustment[];
}

export function ProfileImpactCallout({ adjustments }: ProfileImpactCalloutProps) {
  if (adjustments.length === 0) return null;

  return (
    <div className="rounded-xl border border-teal-200 bg-teal-50 p-4">
      <p className="text-sm font-semibold text-teal-900">Your profile affects these estimates</p>
      <ul className="mt-2 space-y-1 text-sm text-teal-900">
        {adjustments.map((item) => (
          <li key={item.factor}>
            {item.factor} {'->'} {item.impact} (+{formatINRShort(item.cost_delta_min)} to {formatINRShort(item.cost_delta_max)})
          </li>
        ))}
      </ul>
    </div>
  );
}
