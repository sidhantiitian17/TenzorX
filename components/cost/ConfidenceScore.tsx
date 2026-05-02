'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Info } from 'lucide-react';
import { getConfidenceLabel } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
  const [open, setOpen] = useState(false);
  const percentage = Math.round(confidence * 100);
  const label = getConfidenceLabel(confidence);
  const isCompact = size === 'sm';

  const getColor = () => {
    if (confidence < 0.4) {
      return {
        stroke: 'stroke-destructive',
        bar: 'bg-red-500',
        text: 'text-red-700 dark:text-red-300',
        bg: 'bg-red-100/70 dark:bg-red-500/15',
      };
    }
    if (confidence < 0.7) {
      return {
        stroke: 'stroke-amber-500',
        bar: 'bg-amber-500',
        text: 'text-amber-700 dark:text-amber-300',
        bg: 'bg-amber-100/70 dark:bg-amber-500/15',
      };
    }
    return {
      stroke: 'stroke-success',
      bar: 'bg-emerald-500',
      text: 'text-emerald-700 dark:text-emerald-300',
      bg: 'bg-emerald-100/70 dark:bg-emerald-500/15',
    };
  };

  const colors = getColor();

  const sizes = {
    md: { container: 'w-24 h-12', strokeWidth: 3.5, fontSize: 'text-sm', radius: 20 },
    lg: { container: 'w-32 h-16', strokeWidth: 4, fontSize: 'text-base', radius: 28 },
  };

  const s = size === 'lg' ? sizes.lg : sizes.md;
  const circumference = Math.PI * s.radius;
  const offset = circumference - (confidence * circumference);

  return (
    <TooltipProvider>
      <>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              className={cn(
                'rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                isCompact ? 'inline-flex' : 'flex flex-col items-center gap-1'
              )}
              onClick={() => {
                onClick?.();
                setOpen(true);
              }}
              aria-label={`Confidence ${percentage}% ${label}`}
            >
              {isCompact ? (
                <div className={cn('min-w-24 rounded-lg border border-border/70 px-3 py-2 shadow-sm', colors.bg)}>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                        Confidence
                      </span>
                      <div className="flex items-baseline gap-1 mt-0.5">
                        <span className={cn('font-mono text-lg font-bold tabular-nums leading-none', colors.text)}>
                          {percentage}%
                        </span>
                        {showLabel && (
                          <span className={cn('text-xs font-medium', colors.text)}>{label}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 h-1.5 w-full rounded-full bg-black/10 dark:bg-white/15">
                    <motion.div
                      className={cn('h-full rounded-full', colors.bar)}
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.8, ease: 'easeOut' }}
                    />
                  </div>
                </div>
              ) : (
                <>
                  <div className={cn('relative rounded-md px-1.5', s.container, colors.bg)}>
                    {/* Background circle */}
                    <svg className="h-full w-full" viewBox="0 0 100 52">
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
                      <span className={cn('font-mono font-bold tabular-nums', s.fontSize, colors.text)}>
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
                </>
              )}
              {isCompact && (
                <div className="sr-only">
                  {label}
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

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Confidence Score: {percentage}%</DialogTitle>
            </DialogHeader>

            <p className="text-sm text-muted-foreground">
              {label} confidence means the estimate is grounded in available benchmark data, but the final cost can still vary by hospital, room choice, and patient complexity.
            </p>

            <div className="space-y-3 text-sm">
              <FactorRow label="Data availability" value="High where city benchmarks are dense" />
              <FactorRow label="Pricing consistency" value="Moderate spread across providers" />
              <FactorRow label="Benchmark recency" value="Recent enough for practical decision support" />
              <FactorRow label="Patient complexity" value="Age and comorbidities can widen the range" />
            </div>

            <Button className="w-full" onClick={() => setOpen(false)}>
              Close
            </Button>
          </DialogContent>
        </Dialog>
      </>
    </TooltipProvider>
  );
}

function FactorRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border px-3 py-2">
      <p className="font-medium">{label}</p>
      <p className="text-muted-foreground">{value}</p>
    </div>
  );
}
