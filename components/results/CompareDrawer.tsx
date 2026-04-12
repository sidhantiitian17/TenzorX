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

  const comparisonRows: Array<{
    label: string;
    highlight?: boolean;
    render: (h: Hospital) => React.ReactNode;
    exportValue?: (h: Hospital) => string;
  }> = [
    {
      label: 'Rating',
      highlight: true,
      render: (h: Hospital) => (
        <div className="flex items-center gap-1">
          <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
          <span className="font-medium">{h.rating}</span>
        </div>
      ),
      exportValue: (h: Hospital) => String(h.rating),
    },
    {
      label: 'Total Cost',
      highlight: true,
      render: (h: Hospital) => (
        <span className="font-mono font-medium">{formatCostRange(h.cost_range)}</span>
      ),
      exportValue: (h: Hospital) => formatCostRange(h.cost_range),
    },
    {
      label: 'Distance',
      render: (h: Hospital) => formatDistance(h.distance_km),
      exportValue: (h: Hospital) => formatDistance(h.distance_km),
    },
    {
      label: 'Confidence',
      highlight: true,
      render: (h: Hospital) => `${Math.round((h.confidence ?? 0.6) * 100)}%`,
      exportValue: (h: Hospital) => `${Math.round((h.confidence ?? 0.6) * 100)}%`,
    },
    {
      label: 'NABH Accredited',
      render: (h: Hospital) =>
        h.nabh_accredited ? (
          <Check className="h-5 w-5 text-emerald-500" />
        ) : (
          <X className="h-5 w-5 text-muted-foreground" />
        ),
      exportValue: (h: Hospital) => (h.nabh_accredited ? 'Yes' : 'No'),
    },
    {
      label: 'Hospital Tier',
      render: (h: Hospital) => getTierLabel(h.tier),
      exportValue: (h: Hospital) => getTierLabel(h.tier),
    },
    {
      label: 'Procedure Volume',
      render: (h: Hospital) => (h.procedure_volume ? h.procedure_volume : 'Unknown'),
      exportValue: (h: Hospital) => (h.procedure_volume ? h.procedure_volume : 'Unknown'),
    },
    {
      label: 'ICU Available',
      highlight: true,
      render: (h: Hospital) => (
        <span className={h.icu_available ? 'text-emerald-600' : 'text-red-600 font-medium'}>
          {h.icu_available ? 'Yes' : 'No'}
        </span>
      ),
      exportValue: (h: Hospital) => (h.icu_available ? 'Yes' : 'No'),
    },
    {
      label: 'Specializations',
      render: (h: Hospital) => h.specializations.slice(0, 2).join(', '),
      exportValue: (h: Hospital) => h.specializations.slice(0, 2).join(', '),
    },
    {
      label: 'Best For',
      render: (h: Hospital) => h.strengths[0] ?? 'Balanced care',
      exportValue: (h: Hospital) => h.strengths[0] ?? 'Balanced care',
    },
  ];

  const exportCsv = () => {
    const headers = ['Attribute', ...hospitals.map((h) => h.name)];
    const rows = comparisonRows.map((row) => [
      row.label,
      ...hospitals.map((hospital) => (row.exportValue ? row.exportValue(hospital) : String(row.render(hospital)))),
    ]);
    const content = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'healthnav-comparison.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportJson = () => {
    const payload = {
      generatedAt: new Date().toISOString(),
      bestValueHospitalId: bestValueId,
      hospitals: hospitals.map((h) => ({
        id: h.id,
        name: h.name,
        city: h.city,
        rating: h.rating,
        costRange: h.cost_range,
        distanceKm: h.distance_km,
        confidence: Math.round((h.confidence ?? 0.6) * 100),
        nabhAccredited: h.nabh_accredited,
        tier: h.tier,
        procedureVolume: h.procedure_volume,
        icuAvailable: h.icu_available,
        bestFor: h.strengths[0] ?? 'Balanced care',
      })),
      disclaimer: 'HealthNav provides decision support only. Confirm with hospitals directly before making decisions.',
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'healthnav-comparison.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportSummary = () => {
    const lines = [
      'HealthNav Hospital Comparison',
      `Best Value Hospital ID: ${bestValueId}`,
      '',
      ...hospitals.map((h) => {
        const confidence = Math.round((h.confidence ?? 0.6) * 100);
        return [
          `${h.name} (${h.city})`,
          `- Rating: ${h.rating}`,
          `- Cost: ${formatCostRange(h.cost_range)}`,
          `- Distance: ${formatDistance(h.distance_km)}`,
          `- Confidence: ${confidence}%`,
          `- NABH: ${h.nabh_accredited ? 'Yes' : 'No'}`,
          `- ICU Available: ${h.icu_available ? 'Yes' : 'No'}`,
          `- Best For: ${h.strengths[0] ?? 'Balanced care'}`,
          '',
        ].join('\n');
      }),
      'Decision support only. Get direct quotes before final decision.',
    ];

    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'healthnav-comparison-summary.txt';
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
                  <th className="sticky left-0 z-20 w-36 bg-card px-4 py-3 text-left font-medium text-muted-foreground">
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
                  // Keep the first column sticky so mobile horizontal scrolling keeps context visible.
                  <tr
                    key={row.label}
                    className={cn(
                      'border-b border-border',
                      index % 2 === 0 && 'bg-muted/20',
                      row.highlight && 'bg-amber-50/50'
                    )}
                  >
                    <td className={cn(
                      'sticky left-0 z-10 px-4 py-3 text-sm text-muted-foreground',
                      index % 2 === 0 ? 'bg-muted/20' : 'bg-card',
                      row.highlight && 'bg-amber-50/80'
                    )}>
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

          <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border px-4 py-3">
            <Button size="sm" variant="outline" onClick={exportCsv}>
              Export CSV
            </Button>
            <Button size="sm" variant="outline" onClick={exportJson}>
              Export JSON
            </Button>
            <Button size="sm" variant="outline" onClick={exportSummary}>
              Export Summary
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
