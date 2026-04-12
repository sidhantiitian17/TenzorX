'use client';

import { motion } from 'framer-motion';
import { Info } from 'lucide-react';
import { getConfidenceLabel } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ConfidenceScoreProps {
  confidence: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  onClick?: () => void;
}

export function ConfidenceScore({
  confidence,
  size = 'md',
  showLabel = true,
  onClick,
}: ConfidenceScoreProps) {
  const percentage = Math.round(confidence * 100);
  const label = getConfidenceLabel(confidence);

  const getColor = () => {
    if (confidence < 0.4) return { stroke: 'stroke-destructive', text: 'text-red-700 dark:text-red-300', bg: 'bg-destructive/10' };
    if (confidence < 0.7) return { stroke: 'stroke-amber-500', text: 'text-amber-700 dark:text-amber-300', bg: 'bg-amber-100/70 dark:bg-amber-500/15' };
    return { stroke: 'stroke-success', text: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-100/70 dark:bg-emerald-500/15' };
  };

  const colors = getColor();

  const sizes = {
    sm: { container: 'w-20 h-10', strokeWidth: 3, fontSize: 'text-sm', radius: 14 },
    md: { container: 'w-24 h-12', strokeWidth: 3.5, fontSize: 'text-sm', radius: 20 },
    lg: { container: 'w-32 h-16', strokeWidth: 4, fontSize: 'text-base', radius: 28 },
  };

  const s = sizes[size];
  const circumference = Math.PI * s.radius;
  const offset = circumference - (confidence * circumference);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button className="flex flex-col items-center gap-1" onClick={onClick} aria-label={`Confidence ${percentage}% ${label}`}>
            <div className={cn('relative rounded-md px-1.5', s.container, colors.bg)}>
              {/* Background circle */}
              <svg className="w-full h-full" viewBox="0 0 100 52">
                <title>{`Confidence ${percentage}% ${label}`}</title>
                <circle
                  cx="50"
                  cy="50"
                  r={s.radius}
                  fill="none"
                  className="stroke-muted"
                  strokeWidth={s.strokeWidth}
                  strokeDasharray={circumference}
                  strokeDashoffset={0}
                  transform="rotate(180 50 50)"
                />
                {/* Progress arc */}
                <motion.circle
                  cx="50"
                  cy="50"
                  r={s.radius}
                  fill="none"
                  className={colors.stroke}
                  strokeWidth={s.strokeWidth}
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: offset }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  transform="rotate(180 50 50)"
                />
              </svg>
              {/* Percentage text */}
              <div className="absolute inset-0 flex items-end justify-center pb-0.5">
                <span className={cn('font-bold tabular-nums font-mono', s.fontSize, colors.text)}>
                  {percentage}%
                </span>
              </div>
            </div>
            {showLabel && (
              <div className="flex items-center gap-1">
                <span className={cn('text-xs font-medium', colors.text)}>{label}</span>
                <Info className="h-3 w-3 text-muted-foreground" />
              </div>
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <p className="text-sm">
            Confidence score reflects data availability, procedure complexity, and regional pricing variability.
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
