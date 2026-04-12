'use client';

import type { Hospital } from '@/types';
import { HospitalCard } from './HospitalCard';

interface HospitalListProps {
  hospitals: Hospital[];
  procedure?: string;
  confidence?: number;
  selectedIds?: string[];
  onToggleCompare?: (id: string) => void;
}

export function HospitalList({
  hospitals,
  procedure,
  confidence,
  selectedIds = [],
  onToggleCompare,
}: HospitalListProps) {
  if (hospitals.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-foreground">
          {hospitals.length} Hospital{hospitals.length !== 1 ? 's' : ''} Found
        </h3>
      </div>
      <div className="space-y-4">
        {hospitals.map((hospital) => (
          <HospitalCard
            key={hospital.id}
            hospital={hospital}
            procedure={procedure}
            confidence={confidence}
            isSelected={selectedIds.includes(hospital.id)}
            onToggleCompare={onToggleCompare}
          />
        ))}
      </div>
    </div>
  );
}
