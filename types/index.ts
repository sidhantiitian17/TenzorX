// Chat Types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  searchData?: SearchData;
  isEmergency?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

// Clinical Mapping Types
export interface PathwayStep {
  step: number;
  name: string;
  duration: string;
  cost_range: CostRange;
  description?: string;
}

export interface ClinicalMapping {
  user_query: string;
  procedure: string;
  icd10_code: string;
  icd10_label: string;
  snomed_code: string;
  category: string;
  pathway: PathwayStep[];
  confidence: number;
}

// Hospital Types
export interface RankSignals {
  clinical_capability: number;  // 0-100
  reputation: number;
  accessibility: number;
  affordability: number;
}

export interface SentimentTheme {
  theme: string;
  mentions: number;
  positive_pct: number;
}

export interface SentimentData {
  positive_pct: number;
  themes: SentimentTheme[];
  sample_quotes: { text: string; sentiment: 'positive' | 'concern' }[];
}

export interface Hospital {
  id: string;
  name: string;
  location: string;
  city: string;
  distance_km: number;
  rating: number;
  review_count?: number;
  tier: 'premium' | 'mid' | 'budget';
  nabh_accredited: boolean;
  specializations: string[];
  strengths: string[];
  risk_flags?: string[];
  cost_range: CostRange;
  confidence?: number;
  doctors: Doctor[];
  reviews: Review[];
  logo?: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  rank_score?: number;
  rank_signals?: RankSignals;
  sentiment_data?: SentimentData;
  procedure_volume?: 'high' | 'medium' | 'low';
  icu_available?: boolean;
  wait_time_days?: number;
}

export interface Doctor {
  id: string;
  name: string;
  specialization: string;
  experience_years: number;
  qualification?: string;
  rating?: number;
  fee_min?: number;
  fee_max?: number;
}

export interface Review {
  id: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  excerpt: string;
}

export type Accreditation = 'NABH' | 'NABL' | 'JCI';

// Cost Types
export interface CostRange {
  min: number;
  max: number;
}

export interface CostBreakdown {
  procedure: CostRange;
  doctor_fees: CostRange;
  hospital_stay: CostRange & { nights?: string };
  diagnostics: CostRange;
  medicines: CostRange;
  contingency: CostRange;
}

export interface GeoAdjustment {
  city_tier: 'metro' | 'tier2' | 'tier3';
  city_name: string;
  discount_vs_metro: number;
}

export interface RiskAdjustment {
  factor: string;
  impact: string;
  cost_delta_min: number;
  cost_delta_max: number;
  severity: 'high' | 'medium' | 'low';
}

export interface CostEstimate {
  procedure: string;
  icd10_code: string;
  location?: string;
  tier?: 'premium' | 'mid' | 'budget';
  cost_range: CostRange;
  typical_range?: CostRange;
  confidence: number;
  cost_breakdown: CostBreakdown;
  comorbidity_warnings: string[];
  geo_adjustment?: GeoAdjustment;
  risk_adjustments?: RiskAdjustment[];
  data_sources?: string[];
}

// Search Data from AI response
export interface SearchData {
  procedure: string;
  icd10_code: string;
  icd10_label?: string;
  snomed_code?: string;
  category?: string;
  query_location: string;
  cost_range: CostRange;
  confidence: number;
  cost_breakdown: CostBreakdown;
  comorbidity_warnings: string[];
  hospitals: Hospital[];
  clinical_mapping?: ClinicalMapping;
  geo_adjustment?: GeoAdjustment;
  risk_adjustments?: RiskAdjustment[];
  data_sources?: string[];
  pathway?: PathwayStep[];
}

// Patient Profile
export interface PatientProfile {
  age: number | null;
  gender: 'male' | 'female' | 'other' | 'prefer_not_to_say' | null;
  comorbidities: string[];
  budget_min: number;
  budget_max: number;
  location: string;
}

// Lender Mode Types
export interface LenderRiskProfile {
  procedure: string;
  icd10_code: string;
  risk_level: 'low' | 'moderate' | 'high';
  base_estimate: CostRange;
  comorbidity_adjustment: CostRange;
  max_foreseeable_cost: CostRange;
  recommended_cover: CostRange;
  confidence: number;
  risk_factors: {
    factor: string;
    severity: 'high' | 'medium' | 'low';
    impact: string;
  }[];
  procedure_risk: {
    mortality_risk: string;
    icu_probability: string;
    avg_los_days: string;
    readmission_rate: string;
  };
}

// Medical Term Explainer
export interface MedicalTerm {
  term: string;
  simple_explanation: string;
  analogy?: string;
  when_needed?: string;
  procedure_duration?: string;
  hospital_stay?: string;
  recovery_time?: string;
  icd10_code?: string;
  snomed_code?: string;
  related_terms?: string[];
}

// Appointment Guide
export interface AppointmentChecklist {
  documents: { item: string; checked: boolean }[];
  questions: string[];
  forms: string[];
}

// App State
export interface AppState {
  conversation: Message[];
  searchResults: Hospital[];
  costEstimate: CostEstimate | null;
  clinicalMapping: ClinicalMapping | null;
  patientProfile: PatientProfile | null;
  selectedForCompare: string[];
  savedHospitals: string[];
  isLoading: boolean;
  error: string | null;
  activeQuery: string;
  sidebarOpen: boolean;
  compareDrawerOpen: boolean;
  resultsPanelOpen: boolean;
  lenderMode: boolean;
  lenderRiskProfile: LenderRiskProfile | null;
}

export type AppAction =
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'SET_SEARCH_RESULTS'; payload: Hospital[] }
  | { type: 'SET_COST_ESTIMATE'; payload: CostEstimate | null }
  | { type: 'SET_CLINICAL_MAPPING'; payload: ClinicalMapping | null }
  | { type: 'SET_PATIENT_PROFILE'; payload: PatientProfile | null }
  | { type: 'TOGGLE_COMPARE'; payload: string }
  | { type: 'TOGGLE_SAVE'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_ACTIVE_QUERY'; payload: string }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'TOGGLE_COMPARE_DRAWER' }
  | { type: 'TOGGLE_RESULTS_PANEL' }
  | { type: 'SET_LENDER_MODE'; payload: boolean }
  | { type: 'SET_LENDER_RISK_PROFILE'; payload: LenderRiskProfile | null }
  | { type: 'CLEAR_CONVERSATION' }
  | { type: 'CLEAR_COMPARE' };
