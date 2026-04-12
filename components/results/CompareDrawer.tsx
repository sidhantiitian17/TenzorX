'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Star, Check, MapPin, Award } from 'lucide-react';
import type { Hospital } from '@/types';
import { calculateBestValueScore, formatCostRange, formatDistance, getTierLabel } from '@/lib/formatters';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface CompareDrawerProps {
  hospitals: Hospital[];
  isOpen: boolean;
  onClose: () => void;
  onRemove: (id: string) => void;
  onClearAll?: () => void;
}

export function CompareDrawer({
  hospitals,
  isOpen,
  onClose,
  onRemove,
  onClearAll,
}: CompareDrawerProps) {
  if (hospitals.length < 2) {
    return null;
  }

  // Weighted best-value score: Rating (0.4) + inverse cost (0.3) + confidence (0.3)
  const bestValueId = hospitals.reduce((best, hospital) => {
    const avgCost = (hospital.cost_range.min + hospital.cost_range.max) / 2;
    const valueScore = calculateBestValueScore(hospital.rating, avgCost, hospital.confidence ?? 0.6);
    const bestHospital = hospitals.find((h) => h.id === best);
    if (!bestHospital) return hospital.id;
    const bestAvgCost = (bestHospital.cost_range.min + bestHospital.cost_range.max) / 2;
    const bestValueScore = calculateBestValueScore(
      bestHospital.rating,
      bestAvgCost,
      bestHospital.confidence ?? 0.6
    );
    return valueScore > bestValueScore ? hospital.id : best;
  }, hospitals[0].id);

  const comparisonRows = [
    {
      label: 'Rating',
      render: (h: Hospital) => (
        <div className="flex items-center gap-1">
          <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
          <span className="font-medium">{h.rating}</span>
        </div>
      ),
    },
    {
      label: 'Estimated Cost',
      render: (h: Hospital) => (
        <span className="font-mono font-medium">{formatCostRange(h.cost_range)}</span>
      ),
    },
    {
      label: 'Distance',
      render: (h: Hospital) => formatDistance(h.distance_km),
    },
    {
      label: 'NABH Accredited',
      render: (h: Hospital) =>
        h.nabh_accredited ? (
          <Check className="h-5 w-5 text-emerald-500" />
        ) : (
          <X className="h-5 w-5 text-muted-foreground" />
        ),
    },
    {
      label: 'Hospital Tier',
      render: (h: Hospital) => getTierLabel(h.tier),
    },
    {
      label: 'Specializations',
      render: (h: Hospital) => h.specializations.slice(0, 2).join(', '),
    },
  ];

  const exportComparison = () => {
    const headers = ['Attribute', ...hospitals.map((h) => h.name)];
    const rows = [
      ['Rating', ...hospitals.map((h) => String(h.rating))],
      ['Cost', ...hospitals.map((h) => formatCostRange(h.cost_range))],
      ['Distance', ...hospitals.map((h) => formatDistance(h.distance_km))],
      ['NABH', ...hospitals.map((h) => (h.nabh_accredited ? 'Yes' : 'No'))],
      ['Tier', ...hospitals.map((h) => getTierLabel(h.tier))],
    ];
    const content = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'healthnav-comparison.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="fixed bottom-0 left-0 right-0 z-50 bg-card border-t border-border shadow-2xl rounded-t-2xl max-h-[70vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <h2 className="font-semibold">Compare Hospitals</h2>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Scrollable content */}
          <div className="overflow-x-auto overflow-y-auto max-h-[calc(70vh-60px)]">
            <table className="w-full min-w-150">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 w-36">
                    Attribute
                  </th>
                  {hospitals.map((hospital) => (
                    <th
                      key={hospital.id}
                      className="text-left font-medium px-4 py-3 min-w-45"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="truncate">{hospital.name}</span>
                            {hospital.id === bestValueId && (
                              <Badge className="bg-emerald-100 text-emerald-700 gap-1">
                                <Award className="h-3 w-3" />
                                Best Value
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground font-normal mt-0.5">
                            {hospital.city}
                          </p>
                        </div>
                        <button
                          onClick={() => onRemove(hospital.id)}
                          className="text-muted-foreground hover:text-foreground p-1 -mr-1"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparisonRows.map((row, index) => (
                  <tr
                    key={row.label}
                    className={cn(
                      'border-b border-border',
                      index % 2 === 0 && 'bg-muted/20'
                    )}
                  >
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {row.label}
                    </td>
                    {hospitals.map((hospital) => (
                      <td key={hospital.id} className="px-4 py-3 text-sm">
                        {row.render(hospital)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
            <Button size="sm" variant="outline" onClick={exportComparison}>
              Export Comparison
            </Button>
            <Button size="sm" variant="outline" onClick={onClearAll}>
              Start Over
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Floating compare button for mobile
interface CompareButtonProps {
  count: number;
  onClick: () => void;
}

export function CompareButton({ count, onClick }: CompareButtonProps) {
  if (count < 2) {
    return null;
  }

  return (
    <motion.button
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      onClick={onClick}
      className="fixed bottom-20 left-1/2 -translate-x-1/2 z-40 bg-primary text-primary-foreground px-6 py-3 rounded-full shadow-lg font-medium flex items-center gap-2"
    >
      Compare {count} hospitals
    </motion.button>
  );
}
