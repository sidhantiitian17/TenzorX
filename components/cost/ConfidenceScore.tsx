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
      <>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              className="flex flex-col items-center gap-1"
              onClick={() => {
                onClick?.();
                setOpen(true);
              }}
              aria-label={`Confidence ${percentage}% ${label}`}
            >
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
