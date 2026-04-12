'use client';

interface HighVarianceWarningProps {
  confidence: number;
  spreadRatio: number;
}

export function HighVarianceWarning({ confidence, spreadRatio }: HighVarianceWarningProps) {
  const shouldShow = confidence < 0.4 || spreadRatio > 2;
  if (!shouldShow) return null;

  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900">
      <p className="text-sm font-semibold">Wide Cost Variation Warning</p>
      <p className="mt-1 text-sm">
        Cost estimates for this procedure vary significantly across hospitals and patient profiles.
        We recommend getting quotes from 2 to 3 hospitals before making a decision.
      </p>
    </div>
  );
}
