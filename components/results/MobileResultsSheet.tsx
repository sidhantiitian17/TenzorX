'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronDown } from 'lucide-react';
import type { Hospital, CostEstimate, ClinicalMapping } from '@/types';
import { HospitalList } from './HospitalList';
import { PathwayVisualizer } from './PathwayVisualizer';
import { ResultsControls } from './ResultsControls';
import { CostEstimateCard } from '@/components/cost/CostEstimateCard';
import { Button } from '@/components/ui/button';
import { ClinicalMappingCard } from './ClinicalMappingCard';
import { useAppState } from '@/lib/context';

interface MobileResultsSheetProps {
  hospitals: Hospital[];
  costEstimate: CostEstimate | null;
  clinicalMapping?: ClinicalMapping | null;
  onCorrectMapping?: () => void;
  selectedIds: string[];
  onToggleCompare: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function MobileResultsSheet({
  hospitals,
  costEstimate,
  clinicalMapping,
  onCorrectMapping,
  selectedIds,
  onToggleCompare,
  isOpen,
  onClose,
}: MobileResultsSheetProps) {
  const appState = useAppState();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-background rounded-t-2xl max-h-[90vh] overflow-hidden lg:hidden"
          >
            {/* Handle */}
            <div className="flex justify-center pt-2 pb-1">
              <div className="w-10 h-1 bg-muted-foreground/30 rounded-full" />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-border">
              <h2 className="font-semibold">Results</h2>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <ChevronDown className="h-4 w-4 mr-1" />
                Close
              </Button>
            </div>

            <ResultsControls totalCount={appState.searchResults.length} visibleCount={hospitals.length} />

            {/* Content */}
            <div className="overflow-y-auto max-h-[calc(90vh-80px)] p-4 space-y-6 custom-scrollbar">
              {clinicalMapping && (
                <ClinicalMappingCard
                  mapping={clinicalMapping}
                  onCorrect={onCorrectMapping ?? (() => undefined)}
                />
              )}
              {clinicalMapping?.pathway && clinicalMapping.pathway.length > 0 && (
                <PathwayVisualizer pathway={clinicalMapping.pathway} />
              )}
              {costEstimate && (
                <CostEstimateCard
                  estimate={costEstimate}
                  comorbidityWarnings={costEstimate.comorbidity_warnings}
                />
              )}
              {hospitals.length > 0 && (
                <HospitalList
                  hospitals={hospitals}
                  procedure={costEstimate?.procedure}
                  confidence={costEstimate?.confidence}
                  selectedIds={selectedIds}
                  onToggleCompare={onToggleCompare}
                />
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Floating button to open results on mobile
interface MobileResultsButtonProps {
  count: number;
  onClick: () => void;
}

export function MobileResultsButton({ count, onClick }: MobileResultsButtonProps) {
  if (count === 0) {
    return null;
  }

  return (
    <motion.button
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      onClick={onClick}
      className="fixed bottom-24 left-1/2 -translate-x-1/2 z-40 bg-primary text-primary-foreground px-6 py-3 rounded-full shadow-lg font-medium lg:hidden"
    >
      View Results ({count} hospital{count !== 1 ? 's' : ''})
    </motion.button>
  );
}
