'use client';

import { useCallback, useMemo, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useAppDispatch, useAppState, useCompare } from '@/lib/context';
import { buildCostEstimate, buildLenderRiskProfile, generateMockSearchData } from '@/lib/mockData';
import type { Message } from '@/types';

import { DisclaimerBanner } from '@/components/shared/DisclaimerBanner';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { ResultsPanel } from '@/components/results/ResultsPanel';
import { CompareDrawer } from '@/components/results/CompareDrawer';
import { CompareBar } from '@/components/results/CompareBar';
import { MobileResultsSheet, MobileResultsButton } from '@/components/results/MobileResultsSheet';
import { PatientProfileModal } from '@/components/profile/PatientProfileModal';
import { LenderDashboard } from '@/components/lender/LenderDashboard';

const EMERGENCY_TERMS = [
  'chest pain',
  'stroke',
  'unconscious',
  'heavy bleeding',
  "can't breathe",
  'severe pain',
  'heart attack',
];

export default function HomePage() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { selectedIds, toggleCompare, count: compareCount } = useCompare();

  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [mobileResultsOpen, setMobileResultsOpen] = useState(false);
  const [showEmergency, setShowEmergency] = useState(false);

  const selectedHospitals = useMemo(
    () => state.searchResults.filter((h: { id: string }) => selectedIds.includes(h.id)),
    [selectedIds, state.searchResults]
  );

  const handleSendMessage = useCallback(
    async (content: string) => {
      const query = content.trim();
      if (!query) return;

      const isEmergency = EMERGENCY_TERMS.some((word) => query.toLowerCase().includes(word));
      setShowEmergency(isEmergency);

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: query,
        timestamp: new Date(),
      };

      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ACTIVE_QUERY', payload: query });

      await new Promise((resolve) => setTimeout(resolve, 900));

      const location = extractLocation(query, state.patientProfile?.location || 'Nagpur');
      const searchData = generateMockSearchData(query, location);

      if (state.patientProfile?.comorbidities.length) {
        searchData.comorbidity_warnings = state.patientProfile.comorbidities.map(
          (condition: string) =>
            `${condition}: may increase complication risk and total estimate spread by Rs 10K to Rs 60K depending on provider.`
        );
      }

      const estimate = buildCostEstimate(searchData);
      const lenderRisk = buildLenderRiskProfile(estimate);

      let response = `I interpreted your query as **${searchData.procedure}** and found **${searchData.hospitals.length} hospitals** in **${searchData.query_location}**.`;
      response += `\n\nEstimated range: **Rs ${searchData.cost_range.min.toLocaleString('en-IN')} - Rs ${searchData.cost_range.max.toLocaleString('en-IN')}** with confidence **${Math.round(searchData.confidence * 100)}%**.`;

      if (isEmergency) {
        response = '**Possible emergency indicators detected. If urgent symptoms are active, call 112 immediately.**\n\n' + response;
      }

      response += '\n\nDecision support only. Please consult a qualified doctor before making medical decisions.';

      const aiMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: new Date(),
        searchData,
      };

      dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
      dispatch({ type: 'SET_SEARCH_RESULTS', payload: searchData.hospitals });
      dispatch({ type: 'SET_COST_ESTIMATE', payload: estimate });
      dispatch({ type: 'SET_CLINICAL_MAPPING', payload: searchData.clinical_mapping || null });
      dispatch({ type: 'SET_LENDER_RISK_PROFILE', payload: lenderRisk });
      dispatch({ type: 'SET_LOADING', payload: false });
    },
    [dispatch, state.patientProfile?.comorbidities, state.patientProfile?.location]
  );

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <DisclaimerBanner />

      <Header onOpenProfile={() => setProfileModalOpen(true)} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          onToggleLenderMode={() =>
            dispatch({ type: 'SET_LENDER_MODE', payload: !state.lenderMode })
          }
          onOpenProfile={() => setProfileModalOpen(true)}
          onOpenSettings={() => {
            // Could open settings modal here
            console.log('Settings clicked');
          }}
          onLoadQuery={(query: string) => handleSendMessage(query)}
        />

        <main className="flex min-w-0 flex-1 flex-col lg:w-[60%]">
          <ChatWindow
            messages={state.conversation}
            isLoading={state.isLoading}
            onSendMessage={handleSendMessage}
            onOpenProfile={() => setProfileModalOpen(true)}
            showEmergency={showEmergency}
            onDismissEmergency={() => setShowEmergency(false)}
          />
        </main>

        {state.lenderMode && state.lenderRiskProfile ? (
          <aside className="hidden w-[40%] max-w-lg overflow-y-auto border-l border-border bg-background p-4 lg:block">
            <LenderDashboard
              profile={state.lenderRiskProfile}
              patientProfile={state.patientProfile}
            />
          </aside>
        ) : (
          <ResultsPanel
            hospitals={state.searchResults}
            costEstimate={state.costEstimate}
            selectedIds={selectedIds}
            onToggleCompare={toggleCompare}
            isOpen={state.resultsPanelOpen}
            clinicalMapping={state.clinicalMapping}
            riskAdjustments={state.costEstimate?.risk_adjustments || []}
            dataSources={state.costEstimate?.data_sources || []}
            onCorrectMapping={() => handleSendMessage('Actually, I meant...')}
            className="hidden w-[40%] max-w-lg lg:flex"
          />
        )}
      </div>

      <AnimatePresence>
        {state.searchResults.length > 0 && !mobileResultsOpen && !state.lenderMode && (
          <MobileResultsButton
            count={state.searchResults.length}
            onClick={() => setMobileResultsOpen(true)}
          />
        )}
      </AnimatePresence>

      <MobileResultsSheet
        hospitals={state.searchResults}
        costEstimate={state.costEstimate}
        selectedIds={selectedIds}
        onToggleCompare={toggleCompare}
        isOpen={mobileResultsOpen}
        onClose={() => setMobileResultsOpen(false)}
      />

      <CompareDrawer
        hospitals={selectedHospitals}
        isOpen={state.compareDrawerOpen}
        onClose={() => dispatch({ type: 'TOGGLE_COMPARE_DRAWER' })}
        onRemove={toggleCompare}
        onClearAll={() => dispatch({ type: 'CLEAR_COMPARE' })}
      />

      <CompareBar
        hospitals={selectedHospitals}
        onRemove={toggleCompare}
        onCompareNow={() => dispatch({ type: 'TOGGLE_COMPARE_DRAWER' })}
      />

      <PatientProfileModal
        open={profileModalOpen}
        onOpenChange={setProfileModalOpen}
        profile={state.patientProfile}
        onSave={(profile) => dispatch({ type: 'SET_PATIENT_PROFILE', payload: profile })}
        onClear={() => dispatch({ type: 'SET_PATIENT_PROFILE', payload: null })}
      />
    </div>
  );
}

function extractLocation(query: string, fallback: string): string {
  const cities = ['nagpur', 'raipur', 'bhopal', 'indore', 'nashik', 'aurangabad', 'surat', 'patna'];
  const match = cities.find((city) => query.toLowerCase().includes(city));
  if (!match) return fallback;
  return match.charAt(0).toUpperCase() + match.slice(1);
}
