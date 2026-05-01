'use client';

import { useCallback, useMemo, useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useAppDispatch, useAppState, useCompare } from '@/lib/context';
import { buildCostEstimate, buildLenderRiskProfile, generateMockSearchData } from '@/lib/mockData';
import {
  callTriageAPI,
  callChatAPI,
  getSessionAPI,
  searchHospitalsAPI,
  transformTriageToSearchData,
  APIError,
} from '@/lib/api';
import type { AppState, Hospital, Message } from '@/types';
import { cn } from '@/lib/utils';

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
  const [resultsExpanded, setResultsExpanded] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const selectedHospitals = useMemo(
    () => state.searchResults.filter((h: { id: string }) => selectedIds.includes(h.id)),
    [selectedIds, state.searchResults]
  );

  const visibleHospitals = useMemo(
    () => applyHospitalFiltersAndSort(state.searchResults, state.sortMode, state.filters),
    [state.filters, state.searchResults, state.sortMode]
  );

  // Load session data on mount (for saved results, appointments, etc.)
  useEffect(() => {
    async function loadSession() {
      try {
        const sessionData = await getSessionAPI(sessionId);
        // Could restore saved results, appointments, etc. from session
        console.log('Session loaded:', sessionData.session_id);
      } catch (e) {
        // Session might not exist yet, which is fine
        console.log('No existing session found, starting fresh');
      }
    }
    loadSession();
  }, [sessionId]);

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

      const location = extractLocation(query, state.patientProfile?.location || 'Nagpur');

      try {
        // Try the new Master Orchestrator API first
        const chatResponse = await callChatAPI(
          query,
          sessionId,
          location,
          state.patientProfile
            ? {
                age: state.patientProfile.age ?? undefined,
                comorbidities: state.patientProfile.comorbidities,
                budget_inr: state.patientProfile.budget_min || state.patientProfile.budget_max || undefined,
                insurance: state.patientProfile.insurance_type ? true : false,
              }
            : undefined
        );

        // Build response from Master Orchestrator output
        let response = chatResponse.chat_response.message;
        const triage = chatResponse.chat_response.triage;
        
        if (isEmergency || triage === 'RED') {
          response = '**🚨 Emergency indicators detected. If urgent symptoms are active, call 112 immediately.**\n\n' + response;
        }

        // Transform hospitals from MasterResponse to frontend format
        const hospitals = chatResponse.hospitals || [];
        const hospitalCount = hospitals.length;

        // Build search data from response
        const searchData: import('@/types').SearchData = {
          procedure: chatResponse.clinical_interpretation?.canonical_procedure || query,
          icd10_code: chatResponse.clinical_interpretation?.icd10 || '',
          icd10_label: chatResponse.clinical_interpretation?.category || '',
          snomed_code: chatResponse.clinical_interpretation?.snomed_ct || '',
          category: chatResponse.clinical_interpretation?.category || 'General Medicine',
          query_location: location,
          cost_range: chatResponse.cost_estimate?.total || { min: 50000, max: 200000 },
          confidence: (chatResponse.chat_response.confidence_score || 75) / 100,
          cost_breakdown: chatResponse.cost_estimate?.components 
            ? {
                procedure: chatResponse.cost_estimate.components['procedure'] || { min: 0, max: 0 },
                doctor_fees: chatResponse.cost_estimate.components['doctor_fees'] || { min: 0, max: 0 },
                hospital_stay: chatResponse.cost_estimate.components['hospital_stay'] || { min: 0, max: 0, nights: '1-2' },
                diagnostics: chatResponse.cost_estimate.components['diagnostics'] || { min: 0, max: 0 },
                medicines: chatResponse.cost_estimate.components['medicines'] || { min: 0, max: 0 },
                contingency: chatResponse.cost_estimate.components['contingency'] || { min: 0, max: 0 },
              }
            : {
                procedure: { min: 0, max: 0 },
                doctor_fees: { min: 0, max: 0 },
                hospital_stay: { min: 0, max: 0, nights: '1-2' },
                diagnostics: { min: 0, max: 0 },
                medicines: { min: 0, max: 0 },
                contingency: { min: 0, max: 0 },
              },
          comorbidity_warnings: chatResponse.treatment_pathway?.comorbidity_note 
            ? [chatResponse.treatment_pathway.comorbidity_note] 
            : [],
          hospitals: hospitals.slice(0, 3),
          clinical_mapping: {
            user_query: query,
            procedure: chatResponse.clinical_interpretation?.canonical_procedure || query,
            icd10_code: chatResponse.clinical_interpretation?.icd10 || '',
            icd10_label: chatResponse.clinical_interpretation?.category || '',
            snomed_code: chatResponse.clinical_interpretation?.snomed_ct || '',
            category: chatResponse.clinical_interpretation?.category || 'General Medicine',
            pathway: (chatResponse.treatment_pathway?.phases || []).map((p, i) => ({
              step: i + 1,
              name: p.phase,
              duration: '1-3 days',
              cost_range: p.cost_range,
              description: p.description,
            })),
            confidence: (chatResponse.chat_response.confidence_score || 75) / 100,
            confidence_factors: (chatResponse.xai_explanation?.shap_waterfall.features || []).map(f => ({
              key: 'data_availability' as const,
              label: f.name,
              score: Math.round(f.contribution * 100),
              weight: f.value,
              note: `Contribution: ${f.contribution.toFixed(2)}`,
            })),
          },
          pathway: (chatResponse.treatment_pathway?.phases || []).map((p, i) => ({
            step: i + 1,
            name: p.phase,
            duration: '1-3 days',
            cost_range: p.cost_range,
            description: p.description,
          })),
          confidence_factors: [],
          geo_adjustment: {
            city_tier: 'tier2',
            city_name: location,
            discount_vs_metro: 0.32,
          },
          tier_comparison: {
            budget: { min: 0, max: 0 },
            mid: chatResponse.cost_estimate?.total || { min: 50000, max: 200000 },
            premium: { min: 0, max: 0 },
          },
          risk_adjustments: [],
          data_sources: [
            'NVIDIA Mistral LLM Analysis',
            'ICD-10 Medical Classification',
            'Healthcare Cost Database',
          ],
        };

        const estimate = buildCostEstimate(searchData);
        const lenderRisk = buildLenderRiskProfile(estimate);

        const aiMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response,
          timestamp: new Date(),
          searchData,
        };

        dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
        dispatch({ type: 'SET_SEARCH_RESULTS', payload: searchData.hospitals });
        dispatch({ type: 'SET_SORT_MODE', payload: 'best-match' });
        dispatch({ type: 'SET_FILTERS', payload: { tier: 'all', nabhOnly: false, distanceKm: null, rating: null } });
        dispatch({ type: 'SET_COST_ESTIMATE', payload: estimate });
        dispatch({ type: 'SET_CLINICAL_MAPPING', payload: searchData.clinical_mapping || null });
        dispatch({ type: 'SET_LENDER_RISK_PROFILE', payload: lenderRisk });
      } catch (error) {
        console.warn('Master Orchestrator API failed, falling back to legacy API:', error);
        
        // Fallback to legacy triage API
        try {
          const triageResponse = await callTriageAPI(
            query,
            state.patientProfile
              ? {
                  age: state.patientProfile.age ?? undefined,
                  location: state.patientProfile.location,
                  known_comorbidities: state.patientProfile.comorbidities,
                }
              : undefined,
            undefined
          );

          let hospitals: Hospital[] = [];
          try {
            hospitals = await searchHospitalsAPI({
              location,
              limit: 3,
              min_rating: 3,
            });
          } catch {
            hospitals = [];
          }

          const searchData = transformTriageToSearchData(triageResponse, hospitals, query, location);

          if (state.patientProfile?.comorbidities.length) {
            searchData.comorbidity_warnings = state.patientProfile.comorbidities.map(
              (condition: string) =>
                `${condition}: may increase complication risk and total estimate spread by Rs 10K to Rs 60K depending on provider.`
            );
          }

          const estimate = buildCostEstimate(searchData);
          const lenderRisk = buildLenderRiskProfile(estimate);
          const hospitalCount = searchData.hospitals.length;
          const hospitalLabel = hospitalCount === 1 ? 'hospital' : 'hospitals';

          let response = triageResponse.agent_response;
          if (response.length < 100 && hospitalCount > 0) {
            response = `I interpreted your query as **${searchData.procedure}** and found **${hospitalCount} ${hospitalLabel}** in **${searchData.query_location}**.\n\n`;
            response += `Estimated range: **Rs ${searchData.cost_range.min.toLocaleString('en-IN')} - Rs ${searchData.cost_range.max.toLocaleString('en-IN')}** with confidence **${Math.round(searchData.confidence * 100)}%**.\n\n`;
            response += triageResponse.agent_response;
          }

          if (isEmergency) {
            response = '**Possible emergency indicators detected. If urgent symptoms are active, call 112 immediately.**\n\n' + response;
          }

          const aiMessage: Message = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: response,
            timestamp: new Date(),
            searchData,
          };

          dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
          dispatch({ type: 'SET_SEARCH_RESULTS', payload: searchData.hospitals });
          dispatch({ type: 'SET_SORT_MODE', payload: 'best-match' });
          dispatch({ type: 'SET_FILTERS', payload: { tier: 'all', nabhOnly: false, distanceKm: null, rating: null } });
          dispatch({ type: 'SET_COST_ESTIMATE', payload: estimate });
          dispatch({ type: 'SET_CLINICAL_MAPPING', payload: searchData.clinical_mapping || null });
          dispatch({ type: 'SET_LENDER_RISK_PROFILE', payload: lenderRisk });
        } catch (fallbackError) {
          // Both APIs failed - use mock data
          console.warn('Both APIs failed, using mock data:', fallbackError);
          await new Promise((resolve) => setTimeout(resolve, 900));

          const searchData = generateMockSearchData(query, location);

          if (state.patientProfile?.comorbidities.length) {
            searchData.comorbidity_warnings = state.patientProfile.comorbidities.map(
              (condition: string) =>
                `${condition}: may increase complication risk and total estimate spread by Rs 10K to Rs 60K depending on provider.`
            );
          }

          const estimate = buildCostEstimate(searchData);
          const lenderRisk = buildLenderRiskProfile(estimate);
          const hospitalCount = searchData.hospitals.length;
          const hospitalLabel = hospitalCount === 1 ? 'hospital' : 'hospitals';

          let response = `I interpreted your query as **${searchData.procedure}** and found **${hospitalCount} ${hospitalLabel}** in **${searchData.query_location}**.`;
          response += `\n\nEstimated range: **Rs ${searchData.cost_range.min.toLocaleString('en-IN')} - Rs ${searchData.cost_range.max.toLocaleString('en-IN')}** with confidence **${Math.round(searchData.confidence * 100)}%**.`;

          if (isEmergency) {
            response = '**Possible emergency indicators detected. If urgent symptoms are active, call 112 immediately.**\n\n' + response;
          }

          response += '\n\n*(Using offline data - backend LLM service unavailable)*';
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
          dispatch({ type: 'SET_SORT_MODE', payload: 'best-match' });
          dispatch({ type: 'SET_FILTERS', payload: { tier: 'all', nabhOnly: false, distanceKm: null, rating: null } });
          dispatch({ type: 'SET_COST_ESTIMATE', payload: estimate });
          dispatch({ type: 'SET_CLINICAL_MAPPING', payload: searchData.clinical_mapping || null });
          dispatch({ type: 'SET_LENDER_RISK_PROFILE', payload: lenderRisk });
        }
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    },
    [dispatch, sessionId, state.patientProfile]
  );

  return (
    <div className="flex min-h-screen flex-col overflow-hidden bg-background">
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

        <main className="flex min-w-0 flex-1 flex-col lg:min-w-120">
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
            hospitals={visibleHospitals}
            costEstimate={state.costEstimate}
            selectedIds={selectedIds}
            onToggleCompare={toggleCompare}
            isOpen={state.resultsPanelOpen}
            expanded={resultsExpanded}
            onToggleExpanded={() => setResultsExpanded((prev) => !prev)}
            clinicalMapping={state.clinicalMapping}
            riskAdjustments={state.costEstimate?.risk_adjustments || []}
            dataSources={state.costEstimate?.data_sources || []}
            onCorrectMapping={() => handleSendMessage('Actually, I meant...')}
            className={cn(
              'hidden lg:flex',
              resultsExpanded
                ? 'w-[56vw] max-w-6xl'
                : 'w-88 max-w-lg xl:w-md 2xl:w-lg'
            )}
          />
        )}
      </div>

      <AnimatePresence>
        {visibleHospitals.length > 0 && !mobileResultsOpen && !state.lenderMode && (
          <MobileResultsButton
            count={visibleHospitals.length}
            onClick={() => setMobileResultsOpen(true)}
          />
        )}
      </AnimatePresence>

      <MobileResultsSheet
        hospitals={visibleHospitals}
        costEstimate={state.costEstimate}
        clinicalMapping={state.clinicalMapping}
        onCorrectMapping={() => handleSendMessage('Actually, I meant...')}
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

function applyHospitalFiltersAndSort(
  hospitals: Hospital[],
  sortMode: AppState['sortMode'],
  filters: AppState['filters']
): Hospital[] {
  const filtered = hospitals.filter((hospital) => {
    if (filters.tier !== 'all' && hospital.tier !== filters.tier) {
      return false;
    }
    if (filters.nabhOnly && !hospital.nabh_accredited) {
      return false;
    }
    if (filters.distanceKm !== null && hospital.distance_km > filters.distanceKm) {
      return false;
    }
    if (filters.rating !== null && hospital.rating < filters.rating) {
      return false;
    }
    return true;
  });

  const sorted = [...filtered];
  sorted.sort((a, b) => {
    if (sortMode === 'lowest-cost') {
      const aMid = (a.cost_range.min + a.cost_range.max) / 2;
      const bMid = (b.cost_range.min + b.cost_range.max) / 2;
      return aMid - bMid;
    }
    if (sortMode === 'highest-rating') {
      return b.rating - a.rating;
    }
    if (sortMode === 'nearest') {
      return a.distance_km - b.distance_km;
    }
    if (sortMode === 'nabh-first') {
      if (a.nabh_accredited !== b.nabh_accredited) {
        return a.nabh_accredited ? -1 : 1;
      }
      return (b.rank_score ?? 0) - (a.rank_score ?? 0);
    }
    return (b.rank_score ?? 0) - (a.rank_score ?? 0);
  });

  return sorted;
}
