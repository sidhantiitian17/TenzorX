'use client';

import { X } from 'lucide-react';
import type { Hospital } from '@/types';
import { Button } from '@/components/ui/button';

interface CompareBarProps {
  hospitals: Hospital[];
  onRemove: (id: string) => void;
  onCompareNow: () => void;
}

export function CompareBar({ hospitals, onRemove, onCompareNow }: CompareBarProps) {
  if (hospitals.length === 0) return null;

  return (
    <div className="fixed bottom-3 left-3 right-3 z-40 rounded-xl border border-border bg-card p-3 shadow-xl lg:left-20 xl:left-72 lg:right-8">
      <div className="flex flex-wrap items-center gap-2">
        <p className="mr-2 text-sm font-medium">Compare</p>
        {hospitals.map((hospital) => (
          <span key={hospital.id} className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 text-xs">
            {hospital.name}
            <button aria-label="Remove" onClick={() => onRemove(hospital.id)}>
              <X className="h-3.5 w-3.5" />
            </button>
          </span>
        ))}
        {hospitals.length < 3 && (
          <span className="inline-flex items-center rounded-full border border-dashed border-border px-2 py-1 text-xs text-muted-foreground">
            + Add ({3 - hospitals.length} slot{3 - hospitals.length !== 1 ? 's' : ''} left)
          </span>
        )}
        <div className="ml-auto">
          <Button size="sm" onClick={onCompareNow} disabled={hospitals.length < 2}>
            Compare Now ({hospitals.length}/3)
          </Button>
        </div>
      </div>
    </div>
  );
}
