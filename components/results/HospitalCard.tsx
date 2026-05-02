'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Star,
  MapPin,
  Building2,
  Stethoscope,
  ChevronDown,
  Check,
  Plus,
  ShieldCheck,
} from 'lucide-react';
import type { Hospital } from '@/types';
import { formatCostRange, formatDistance, getTierLabel, getTierColor } from '@/lib/formatters';
import { ConfidenceScore } from '@/components/cost/ConfidenceScore';
import { CostBreakdown } from '@/components/cost/CostBreakdown';
import { DoctorCard } from './DoctorCard';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { CostBreakdown as CostBreakdownType } from '@/types';

interface HospitalCardProps {
  hospital: Hospital;
  procedure?: string;
  confidence?: number;
  isSelected?: boolean;
  onToggleCompare?: (id: string) => void;
}

export function HospitalCard({
  hospital,
  procedure = 'Procedure',
  confidence = 0.68,
  isSelected = false,
  onToggleCompare,
}: HospitalCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const estimatedBreakdown: CostBreakdownType = {
    procedure: {
      min: Math.round(hospital.cost_range.min * 0.52),
      max: Math.round(hospital.cost_range.max * 0.55),
    },
    doctor_fees: {
      min: Math.round(hospital.cost_range.min * 0.1),
      max: Math.round(hospital.cost_range.max * 0.12),
    },
    hospital_stay: {
      min: Math.round(hospital.cost_range.min * 0.14),
      max: Math.round(hospital.cost_range.max * 0.16),
      nights: '3-5',
    },
    diagnostics: {
      min: Math.round(hospital.cost_range.min * 0.06),
      max: Math.round(hospital.cost_range.max * 0.07),
    },
    medicines: {
      min: Math.round(hospital.cost_range.min * 0.04),
      max: Math.round(hospital.cost_range.max * 0.05),
    },
    contingency: {
      min: Math.round(hospital.cost_range.min * 0.08),
      max: Math.round(hospital.cost_range.max * 0.1),
    },
  };

  const rankingSignals = [
    {
      key: 'clinical_capability' as const,
      label: 'Clinical Capability',
      weight: 35,
      color: 'bg-[var(--c-teal-500)]',
    },
    {
      key: 'reputation' as const,
      label: 'Reputation',
      weight: 30,
      color: 'bg-[var(--c-info)]',
    },
    {
      key: 'accessibility' as const,
      label: 'Accessibility',
      weight: 20,
      color: 'bg-[var(--c-warning)]',
    },
    {
      key: 'affordability' as const,
      label: 'Affordability',
      weight: 15,
      color: 'bg-[var(--c-success)]',
    },
  ];

  const sentimentThemes = hospital.sentiment_data?.themes.slice(0, 5) ?? [];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className={cn(
          'overflow-hidden transition-shadow border-slate-700 bg-slate-800/30',
          isSelected && 'ring-2 ring-teal-500'
        )}
      >
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start gap-4">
            {/* Hospital logo placeholder */}
            <div className="h-12 w-12 rounded-lg bg-teal-500/10 flex items-center justify-center shrink-0">
              <Building2 className="h-6 w-6 text-teal-400" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-slate-100 truncate">
                    {hospital.name}
                  </h3>
                  <p className="text-sm text-slate-400">
                    {hospital.location}
                  </p>
                </div>

                {/* Rating and NABH */}
                <div className="flex items-center gap-2 shrink-0">
                  <div className="flex items-center gap-1 text-sm">
                    <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                    <span className="font-medium text-slate-100">{hospital.rating}</span>
                  </div>
                  {hospital.nabh_accredited && (
                    <Badge variant="secondary" className="bg-emerald-500/20 text-emerald-400 gap-1 border-emerald-500/30">
                      <ShieldCheck className="h-3 w-3" />
                      NABH
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-slate-700 my-4" />

          {/* Procedure and cost */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Procedure: <span className="text-slate-200 font-medium">{procedure}</span>
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">Estimated Cost</p>
                <p className="text-xl font-semibold font-mono text-slate-100">
                  {formatCostRange(hospital.cost_range)}
                </p>
              </div>
              <div className="self-start shrink-0 sm:self-auto">
                <ConfidenceScore confidence={hospital.confidence ?? confidence} size="sm" />
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-slate-700 my-4" />

          {/* Quick info */}
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {formatDistance(hospital.distance_km)}
            </div>
            <Badge variant="secondary" className="bg-slate-700 text-slate-300 border-slate-600">
              {getTierLabel(hospital.tier)}
            </Badge>
            {hospital.specializations.length > 0 && (
              <div className="flex items-center gap-1">
                <Stethoscope className="h-4 w-4" />
                {hospital.specializations[0]}
              </div>
            )}
          </div>

          {hospital.strengths.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {hospital.strengths.slice(0, 3).map((strength) => (
                <Badge key={strength} variant="secondary" className="text-xs bg-slate-700 text-slate-300 border-slate-600">
                  {strength}
                </Badge>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 mt-4">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              View Details
              <ChevronDown
                className={cn(
                  'h-4 w-4 ml-1 transition-transform',
                  isExpanded && 'rotate-180'
                )}
              />
            </Button>
            <Button
              variant={isSelected ? 'default' : 'outline'}
              size="sm"
              className={cn(
                'flex-1',
                isSelected
                  ? 'bg-teal-500 hover:bg-teal-600 text-white'
                  : 'border-slate-600 text-slate-300 hover:bg-slate-700'
              )}
              onClick={() => onToggleCompare?.(hospital.id)}
            >
              {isSelected ? (
                <>
                  <Check className="h-4 w-4 mr-1" />
                  Selected
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-1" />
                  Compare
                </>
              )}
            </Button>
          </div>

          {/* Expanded content */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="pt-4 mt-4 border-t border-border space-y-4">
                  {/* Ranking signal breakdown */}
                  {hospital.rank_signals && (
                    <div>
                      <h4 className="mb-3 text-sm font-medium">Ranking Signal Breakdown</h4>
                      <div className="space-y-2">
                        {rankingSignals.map((signal, index) => {
                          const score = hospital.rank_signals?.[signal.key] ?? 0;
                          return (
                            <div key={signal.key} className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <span className="font-medium text-foreground">
                                  {signal.label} ({signal.weight}%)
                                </span>
                                <span className="font-mono text-muted-foreground">{score}/100</span>
                              </div>
                              <div className="h-2 rounded-full bg-muted">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${score}%` }}
                                  transition={{ duration: 0.5, delay: index * 0.08 }}
                                  className={cn('h-2 rounded-full', signal.color)}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Cost breakdown */}
                  <div>
                    <h4 className="text-sm font-medium mb-3">Cost Breakdown</h4>
                    <CostBreakdown
                      breakdown={estimatedBreakdown}
                      showTable={false}
                    />
                  </div>

                  {/* Doctors */}
                  {hospital.doctors.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Doctors &amp; Appointment Actions</h4>
                      <div className="space-y-2">
                        {hospital.doctors.map((doctor) => (
                          <DoctorCard
                            key={doctor.id}
                            doctor={doctor}
                            hospitalName={hospital.name}
                            procedure={procedure}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Patient voice */}
                  {hospital.sentiment_data && (
                    <div>
                      <h4 className="mb-2 text-sm font-medium">Patient Voice (NLP)</h4>
                      <div className="space-y-2 rounded-md border border-border bg-muted/20 p-3">
                        <p className="text-xs text-muted-foreground">
                          Overall positive sentiment: <span className="font-semibold text-foreground">{hospital.sentiment_data.positive_pct}%</span>
                        </p>
                        <div className="space-y-2">
                          {sentimentThemes.map((theme) => (
                            <div key={theme.theme} className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <span className="font-medium text-foreground">{theme.theme}</span>
                                <span className="text-muted-foreground">{theme.mentions} mentions · {theme.positive_pct}% positive</span>
                              </div>
                              <div className="h-1.5 rounded-full bg-muted">
                                <div className="h-1.5 rounded-full bg-primary" style={{ width: `${theme.positive_pct}%` }} />
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="space-y-1">
                          {hospital.sentiment_data.sample_quotes.slice(0, 2).map((quote, idx) => (
                            <p key={`${quote.text}-${idx}`} className="text-xs italic text-muted-foreground">
                              &quot;{quote.text}&quot; ({quote.sentiment})
                            </p>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {hospital.risk_flags && hospital.risk_flags.length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-medium">Cost Risk Flags</h4>
                      <div className="space-y-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                        {hospital.risk_flags.map((flag) => (
                          <p key={flag}>- {flag}</p>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Strengths */}
                  {hospital.strengths.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Key Strengths</h4>
                      <div className="flex flex-wrap gap-2">
                        {hospital.strengths.map((strength) => (
                          <Badge
                            key={strength}
                            variant="secondary"
                            className="bg-primary/10 text-primary"
                          >
                            {strength}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}
