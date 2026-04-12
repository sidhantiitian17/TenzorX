'use client';

interface DataSourcePanelProps {
  sources: string[];
}

export function DataSourcePanel({ sources }: DataSourcePanelProps) {
  if (sources.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-sm font-semibold">How we built these results</p>
      <div className="mt-3 space-y-2 text-sm text-muted-foreground">
        <p>
          <span className="font-medium text-foreground">Structured data:</span> Hospital directories,
          procedure categories, accreditation registry
        </p>
        <p>
          <span className="font-medium text-foreground">Unstructured data:</span> Patient reviews and
          testimonial sentiment signals
        </p>
        <p>
          <span className="font-medium text-foreground">Derived signals:</span> Regional pricing
          benchmarks, ranking scores, and confidence weighting
        </p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {sources.map((source) => (
          <span key={source} className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
            {source}
          </span>
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground">Last updated: March 2026</p>
    </div>
  );
}
