'use client';

import { MapPin, Search, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  type: 'no-results' | 'error' | 'no-search';
  location?: string;
  onRetry?: () => void;
  onExpandSearch?: () => void;
}

export function EmptyState({ type, location, onRetry, onExpandSearch }: EmptyStateProps) {
  if (type === 'no-results') {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="font-semibold text-foreground mb-2">No hospitals found</h3>
        <p className="text-sm text-muted-foreground max-w-xs mb-6">
          We couldn&apos;t find matching hospitals{location ? ` in ${location}` : ''}. 
          Try expanding your search area or adjusting your filters.
        </p>
        {onExpandSearch && (
          <Button onClick={onExpandSearch} variant="outline">
            <MapPin className="h-4 w-4 mr-2" />
            Search in nearby cities
          </Button>
        )}
      </div>
    );
  }

  if (type === 'error') {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <div className="h-16 w-16 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="font-semibold text-foreground mb-2">Something went wrong</h3>
        <p className="text-sm text-muted-foreground max-w-xs mb-6">
          We encountered an error while fetching results. Please try again.
        </p>
        {onRetry && (
          <Button onClick={onRetry}>
            Try Again
          </Button>
        )}
      </div>
    );
  }

  // no-search default
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <svg
          className="h-8 w-8 text-primary"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      </div>
      <h3 className="font-semibold text-foreground mb-2">No results yet</h3>
      <p className="text-sm text-muted-foreground max-w-xs">
        Describe your condition or procedure to get hospital recommendations and cost estimates.
      </p>
    </div>
  );
}
