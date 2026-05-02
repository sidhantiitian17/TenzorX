'use client';

import { useMemo } from 'react';
import { SlidersHorizontal } from 'lucide-react';
import { useAppDispatch, useAppState } from '@/lib/context';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface ResultsControlsProps {
  totalCount: number;
  visibleCount: number;
}

const sortOptions: Array<{ value: 'best-match' | 'lowest-cost' | 'highest-rating' | 'nearest' | 'nabh-first'; label: string }> = [
  { value: 'best-match', label: 'Best Match' },
  { value: 'lowest-cost', label: 'Lowest Cost' },
  { value: 'highest-rating', label: 'Highest Rating' },
  { value: 'nearest', label: 'Nearest' },
  { value: 'nabh-first', label: 'NABH First' },
];

const tierOptions: Array<{ value: 'all' | 'premium' | 'mid' | 'budget'; label: string }> = [
  { value: 'all', label: 'All Tiers' },
  { value: 'premium', label: 'Premium' },
  { value: 'mid', label: 'Mid-tier' },
  { value: 'budget', label: 'Budget' },
];

export function ResultsControls({ totalCount, visibleCount }: ResultsControlsProps) {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (state.filters.tier !== 'all') count += 1;
    if (state.filters.nabhOnly) count += 1;
    if (state.filters.distanceKm !== null) count += 1;
    if (state.filters.rating !== null) count += 1;
    return count;
  }, [state.filters]);

  return (
    <div className="space-y-3 border-b border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">
          {visibleCount} results{visibleCount !== totalCount ? ` of ${totalCount}` : ''}
        </p>
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => dispatch({ type: 'SET_FILTERS', payload: { tier: 'all', nabhOnly: false, distanceKm: null, rating: null } })}
          >
            Clear Filters ({activeFilterCount})
          </Button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-2 py-1 text-xs text-muted-foreground">
          <SlidersHorizontal className="h-3.5 w-3.5" />
          Sort
        </div>
        <Select
          value={state.sortMode}
          onValueChange={(value) => dispatch({ type: 'SET_SORT_MODE', payload: value as typeof state.sortMode })}
        >
          <SelectTrigger size="sm" className="h-8 min-w-34">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {sortOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={state.filters.distanceKm === null ? 'any' : String(state.filters.distanceKm)}
          onValueChange={(value) =>
            dispatch({
              type: 'SET_FILTERS',
              payload: { distanceKm: value === 'any' ? null : (Number(value) as 5 | 10 | 25) },
            })
          }
        >
          <SelectTrigger size="sm" className="h-8 min-w-28">
            <SelectValue placeholder="Distance" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any Distance</SelectItem>
            <SelectItem value="5">&lt; 5km</SelectItem>
            <SelectItem value="10">&lt; 10km</SelectItem>
            <SelectItem value="25">&lt; 25km</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={state.filters.rating === null ? 'any' : String(state.filters.rating)}
          onValueChange={(value) =>
            dispatch({
              type: 'SET_FILTERS',
              payload: { rating: value === 'any' ? null : (Number(value) as 4 | 4.5) },
            })
          }
        >
          <SelectTrigger size="sm" className="h-8 min-w-26">
            <SelectValue placeholder="Rating" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any Rating</SelectItem>
            <SelectItem value="4">4.0+</SelectItem>
            <SelectItem value="4.5">4.5+</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {tierOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => dispatch({ type: 'SET_FILTERS', payload: { tier: option.value } })}
            className={
              state.filters.tier === option.value
                ? 'rounded-full bg-teal-500 px-3 py-1.5 text-xs font-medium text-white'
                : 'rounded-full bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-200'
            }
          >
            {option.label}
          </button>
        ))}
        <button
          onClick={() => dispatch({ type: 'SET_FILTERS', payload: { nabhOnly: !state.filters.nabhOnly } })}
          className={
            state.filters.nabhOnly
              ? 'rounded-full bg-teal-500 px-3 py-1.5 text-xs font-medium text-white'
              : 'rounded-full bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-200'
          }
        >
          NABH Only
        </button>
      </div>
    </div>
  );
}
