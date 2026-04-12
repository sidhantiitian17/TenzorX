'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Info, Map, List, ChevronsLeft, ChevronsRight } from 'lucide-react';
import type { ClinicalMapping, CostEstimate, Hospital, RiskAdjustment } from '@/types';
import { HospitalList } from './HospitalList';
import { HospitalMap } from './HospitalMap';
import { PathwayVisualizer } from './PathwayVisualizer';
import { ResultsControls } from './ResultsControls';
import { CostEstimateCard } from '@/components/cost/CostEstimateCard';
import { ClinicalMappingCard } from './ClinicalMappingCard';
import { ProfileImpactCallout } from '@/components/profile/ProfileImpactCallout';
import { DataSourcePanel } from '@/components/shared/DataSourcePanel';
import { HighVarianceWarning } from '@/components/shared/HighVarianceWarning';
import { AppointmentGuide } from '@/components/assist/AppointmentGuide';
import { FinancialGuide } from '@/components/assist/FinancialGuide';
import { RankingModal } from './RankingModal';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useAppState } from '@/lib/context';

interface ResultsPanelProps {
  hospitals: Hospital[];
  costEstimate: CostEstimate | null;
  selectedIds: string[];
  onToggleCompare: (id: string) => void;
  isOpen: boolean;
  onClose?: () => void;
  expanded?: boolean;
  onToggleExpanded?: () => void;
  className?: string;
  clinicalMapping?: ClinicalMapping | null;
  riskAdjustments?: RiskAdjustment[];
  dataSources?: string[];
  onCorrectMapping?: () => void;
}

export function ResultsPanel({
  hospitals,
  costEstimate,
  selectedIds,
  onToggleCompare,
  isOpen,
  onClose,
  expanded = false,
  onToggleExpanded,
  className,
  clinicalMapping,
  riskAdjustments = [],
  dataSources = [],
  onCorrectMapping,
}: ResultsPanelProps) {
  const appState = useAppState();
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [selectedHospitalId, setSelectedHospitalId] = useState<string | undefined>();
  const [rankingOpen, setRankingOpen] = useState(false);
  const hasResults = hospitals.length > 0 || costEstimate;

  return (
    <AnimatePresence>
      {isOpen && hasResults && (
        <motion.aside
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={cn(
            'bg-background border-l border-border overflow-hidden flex flex-col lg:sticky lg:top-24 lg:max-h-[calc(100vh-8rem)]',
            className
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
            <div className="flex items-center gap-2">
              <h2 className="font-semibold">Results</h2>
              <button
                className="text-muted-foreground hover:text-foreground"
                onClick={() => setRankingOpen(true)}
                aria-label="Open ranking transparency"
              >
                <Info className="h-4 w-4" />
              </button>
            </div>
            <div className="flex items-center gap-2">
              {onToggleExpanded && (
                <Button
                  variant="outline"
                  size="sm"
                  className="hidden h-7 px-2 lg:inline-flex"
                  onClick={onToggleExpanded}
                >
                  {expanded ? (
                    <>
                      <ChevronsRight className="mr-1 h-3.5 w-3.5" />
                      Collapse
                    </>
                  ) : (
                    <>
                      <ChevronsLeft className="mr-1 h-3.5 w-3.5" />
                      Expand
                    </>
                  )}
                </Button>
              )}
              {/* View Toggle */}
              {hospitals.length > 0 && (
                <div className="flex items-center bg-muted rounded-md p-0.5">
                  <Button
                    variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                    size="sm"
                    className="h-7 px-2"
                    onClick={() => setViewMode('list')}
                  >
                    <List className="h-4 w-4 mr-1" />
                    List
                  </Button>
                  <Button
                    variant={viewMode === 'map' ? 'secondary' : 'ghost'}
                    size="sm"
                    className="h-7 px-2"
                    onClick={() => setViewMode('map')}
                  >
                    <Map className="h-4 w-4 mr-1" />
                    Map
                  </Button>
                </div>
              )}
              {onClose && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 lg:hidden"
                  onClick={onClose}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          <ResultsControls totalCount={appState.searchResults.length} visibleCount={hospitals.length} />

          {/* Content */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {viewMode === 'map' && hospitals.length > 0 ? (
              /* Map View */
              <div className="flex-1 relative">
                <HospitalMap
                  hospitals={hospitals}
                  selectedHospitalId={selectedHospitalId}
                  onHospitalSelect={setSelectedHospitalId}
                  className="h-full"
                />
              </div>
            ) : (
              /* List View */
              <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
                {clinicalMapping && (
                  <ClinicalMappingCard
                    mapping={clinicalMapping}
                    onCorrect={onCorrectMapping ?? (() => undefined)}
                  />
                )}

                {clinicalMapping?.pathway && clinicalMapping.pathway.length > 0 && (
                  <PathwayVisualizer pathway={clinicalMapping.pathway} />
                )}

                {riskAdjustments.length > 0 && <ProfileImpactCallout adjustments={riskAdjustments} />}

                {/* Cost estimate */}
                {costEstimate && (
                  <CostEstimateCard
                    estimate={costEstimate}
                    comorbidityWarnings={costEstimate.comorbidity_warnings}
                  />
                )}

                {costEstimate && (
                  <HighVarianceWarning
                    confidence={costEstimate.confidence}
                    spreadRatio={costEstimate.cost_range.max / Math.max(1, costEstimate.cost_range.min)}
                  />
                )}

                {/* Hospital list */}
                {hospitals.length > 0 && (
                  <HospitalList
                    hospitals={hospitals}
                    procedure={costEstimate?.procedure}
                    confidence={costEstimate?.confidence}
                    selectedIds={selectedIds}
                    onToggleCompare={onToggleCompare}
                  />
                )}

                {costEstimate && <AppointmentGuide procedure={costEstimate.procedure} />}
                <FinancialGuide />
                <DataSourcePanel sources={dataSources} />
              </div>
            )}
          </div>
        </motion.aside>
      )}
      <RankingModal open={rankingOpen} onOpenChange={setRankingOpen} />
    </AnimatePresence>
  );
}

// Empty state component
export function EmptyResultsState() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
      <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
        <svg
          className="h-8 w-8 text-muted-foreground"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      </div>
      <h3 className="font-medium text-foreground mb-1">No results yet</h3>
      <p className="text-sm text-muted-foreground max-w-xs">
        Describe your condition or procedure to get hospital recommendations and cost estimates.
      </p>
    </div>
  );
}
