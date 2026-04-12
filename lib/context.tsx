'use client';

import React, { createContext, useContext, useReducer, type ReactNode } from 'react';
import type { AppState, AppAction, PatientProfile } from '@/types';

const initialState: AppState = {
  conversation: [],
  searchResults: [],
  costEstimate: null,
  clinicalMapping: null,
  patientProfile: null,
  selectedForCompare: [],
  savedHospitals: [],
  isLoading: false,
  error: null,
  activeQuery: '',
  sidebarOpen: false,
  compareDrawerOpen: false,
  resultsPanelOpen: false,
  lenderMode: false,
  lenderRiskProfile: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        conversation: [...state.conversation, action.payload],
      };
    case 'SET_SEARCH_RESULTS':
      return {
        ...state,
        searchResults: action.payload,
        resultsPanelOpen: action.payload.length > 0,
      };
    case 'SET_COST_ESTIMATE':
      return {
        ...state,
        costEstimate: action.payload,
      };
    case 'SET_CLINICAL_MAPPING':
      return {
        ...state,
        clinicalMapping: action.payload,
      };
    case 'SET_PATIENT_PROFILE':
      return {
        ...state,
        patientProfile: action.payload,
      };
    case 'TOGGLE_SAVE': {
      const id = action.payload;
      const exists = state.savedHospitals.includes(id);
      return {
        ...state,
        savedHospitals: exists
          ? state.savedHospitals.filter((savedId) => savedId !== id)
          : [...state.savedHospitals, id],
      };
    }
    case 'TOGGLE_COMPARE':
      const id = action.payload;
      const isSelected = state.selectedForCompare.includes(id);
      if (isSelected) {
        return {
          ...state,
          selectedForCompare: state.selectedForCompare.filter((hId) => hId !== id),
        };
      }
      if (state.selectedForCompare.length >= 3) {
        return state;
      }
      return {
        ...state,
        selectedForCompare: [...state.selectedForCompare, id],
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };
    case 'SET_ACTIVE_QUERY':
      return {
        ...state,
        activeQuery: action.payload,
      };
    case 'TOGGLE_SIDEBAR':
      return {
        ...state,
        sidebarOpen: !state.sidebarOpen,
      };
    case 'TOGGLE_COMPARE_DRAWER':
      return {
        ...state,
        compareDrawerOpen: !state.compareDrawerOpen,
      };
    case 'TOGGLE_RESULTS_PANEL':
      return {
        ...state,
        resultsPanelOpen: !state.resultsPanelOpen,
      };
    case 'SET_LENDER_MODE':
      return {
        ...state,
        lenderMode: action.payload,
      };
    case 'SET_LENDER_RISK_PROFILE':
      return {
        ...state,
        lenderRiskProfile: action.payload,
      };
    case 'CLEAR_CONVERSATION':
      return {
        ...state,
        conversation: [],
        searchResults: [],
        costEstimate: null,
        clinicalMapping: null,
        lenderRiskProfile: null,
        selectedForCompare: [],
        resultsPanelOpen: false,
      };
    case 'CLEAR_COMPARE':
      return {
        ...state,
        selectedForCompare: [],
        compareDrawerOpen: false,
      };
    default:
      return state;
  }
}

const AppStateContext = createContext<AppState | null>(null);
const AppDispatchContext = createContext<React.Dispatch<AppAction> | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppStateContext.Provider value={state}>
      <AppDispatchContext.Provider value={dispatch}>
        {children}
      </AppDispatchContext.Provider>
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within AppProvider');
  }
  return context;
}

export function useAppDispatch() {
  const context = useContext(AppDispatchContext);
  if (!context) {
    throw new Error('useAppDispatch must be used within AppProvider');
  }
  return context;
}

// Convenience hooks
export function usePatientProfile(): [PatientProfile | null, (profile: PatientProfile | null) => void] {
  const state = useAppState();
  const dispatch = useAppDispatch();
  
  const setProfile = (profile: PatientProfile | null) => {
    dispatch({ type: 'SET_PATIENT_PROFILE', payload: profile });
  };

  return [state.patientProfile, setProfile];
}

export function useCompare() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const toggleCompare = (hospitalId: string) => {
    dispatch({ type: 'TOGGLE_COMPARE', payload: hospitalId });
  };

  const clearCompare = () => {
    dispatch({ type: 'CLEAR_COMPARE' });
  };

  const isSelected = (hospitalId: string) => state.selectedForCompare.includes(hospitalId);

  return {
    selectedIds: state.selectedForCompare,
    toggleCompare,
    clearCompare,
    isSelected,
    count: state.selectedForCompare.length,
  };
}
