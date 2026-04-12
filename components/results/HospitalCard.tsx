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

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className={cn(
          'overflow-hidden transition-shadow',
          isSelected && 'ring-2 ring-primary'
        )}
      >
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start gap-4">
            {/* Hospital logo placeholder */}
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <Building2 className="h-6 w-6 text-primary" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-foreground truncate">
                    {hospital.name}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {hospital.location}
                  </p>
                </div>

                {/* Rating and NABH */}
                <div className="flex items-center gap-2 shrink-0">
                  <div className="flex items-center gap-1 text-sm">
                    <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                    <span className="font-medium">{hospital.rating}</span>
                  </div>
                  {hospital.nabh_accredited && (
                    <Badge variant="secondary" className="bg-emerald-100 text-emerald-700 gap-1">
                      <ShieldCheck className="h-3 w-3" />
                      NABH
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-border my-4" />

          {/* Procedure and cost */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Procedure: <span className="text-foreground">{procedure}</span>
              </p>
            </div>

            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Estimated Cost</p>
                <p className="text-xl font-semibold font-mono">
                  {formatCostRange(hospital.cost_range)}
                </p>
              </div>
              <ConfidenceScore confidence={hospital.confidence ?? confidence} size="sm" showLabel={false} />
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-border my-4" />

          {/* Quick info */}
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {formatDistance(hospital.distance_km)}
            </div>
            <Badge variant="secondary" className={getTierColor(hospital.tier)}>
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
                <Badge key={strength} variant="secondary" className="text-xs">
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
              className="flex-1"
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
              className="flex-1"
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
                      <h4 className="text-sm font-medium mb-2">Doctors</h4>
                      <div className="space-y-2">
                        {hospital.doctors.map((doctor) => (
                          <div
                            key={doctor.id}
                            className="flex items-center justify-between text-sm"
                          >
                            <span>{doctor.name}</span>
                            <span className="text-muted-foreground">
                              {doctor.specialization} · {doctor.experience_years} yrs
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reviews */}
                  {hospital.reviews.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Patient Reviews</h4>
                      <div className="space-y-2">
                        {hospital.reviews.slice(0, 2).map((review) => (
                          <p
                            key={review.id}
                            className="text-sm text-muted-foreground italic"
                          >
                            &quot;{review.excerpt}&quot;
                          </p>
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
