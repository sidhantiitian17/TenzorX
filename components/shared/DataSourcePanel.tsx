'use client';

interface DataSourcePanelProps {
  sources: string[];
}

export function DataSourcePanel({ sources }: DataSourcePanelProps) {
  if (sources.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/30 p-4">
      <p className="text-sm font-semibold text-slate-100">How we built these results</p>
      <div className="mt-3 space-y-2 text-sm text-slate-400">
        <p>
          <span className="font-medium text-slate-200">Structured data:</span> Hospital directories,
          procedure categories, accreditation registry
        </p>
        <p>
          <span className="font-medium text-slate-200">Unstructured data:</span> Patient reviews and
          testimonial sentiment signals
        </p>
        <p>
          <span className="font-medium text-slate-200">Derived signals:</span> Regional pricing
          benchmarks, ranking scores, and confidence weighting
        </p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {sources.map((source) => (
          <span key={source} className="rounded-full bg-slate-700 px-2 py-1 text-xs text-slate-400 border border-slate-600">
            {source}
          </span>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-500">Last updated: March 2026</p>
    </div>
  );
}
