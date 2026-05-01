/**
 * API client for TenzorX backend communication.
 * 
 * This module provides functions to call the backend API endpoints.
 * All functions include error handling and fallback mechanisms.
 */

import type { SearchData, Hospital, CostEstimate, LenderRiskProfile, Message } from '@/types';

// Backend API base URL - configurable via environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Timeout for API requests (in milliseconds)
const REQUEST_TIMEOUT = 60000;

/**
 * Error thrown when backend API calls fail
 */
export class APIError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Check if backend API is available
 */
export async function isBackendAvailable(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/`, {
      method: 'GET',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Call the triage endpoint to process a user query through the LLM pipeline
 */
export async function callTriageAPI(
  query: string,
  patientProfile?: {
    age?: number;
    gender?: string;
    location?: string;
    known_comorbidities?: string[];
  },
  financialProfile?: {
    gross_monthly_income?: number;
    existing_emis?: number;
  }
): Promise<{
  severity: 'Red' | 'Yellow' | 'Green';
  rationale: string;
  disclaimer: string;
  icd10_codes: Record<string, string>;
  agent_response: string;
  normalized_query: string;
  cost_estimate?: {
    base_cost: number;
    adjusted_cost: number;
    breakdown: Record<string, number>;
  };
  loan_eligibility?: {
    dti_ratio: number;
    risk_band: string;
    max_recommended_emi: number;
  };
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    // Build request body - only include financial_profile if it has valid data
    const requestBody: Record<string, unknown> = {
      query: query.trim(),
    };

    if (patientProfile && Object.keys(patientProfile).length > 0) {
      requestBody.patient_profile = patientProfile;
    }

    // Only include financial_profile if it has the required fields
    if (financialProfile &&
        typeof financialProfile.gross_monthly_income === 'number' &&
        financialProfile.gross_monthly_income > 0) {
      requestBody.financial_profile = financialProfile;
    }

    const response = await fetch(`${API_BASE_URL}/triage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Triage API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    // Check for AbortController timeout (DOMException with name 'AbortError')
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to call triage API: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Search for hospitals based on location and criteria
 */
export async function searchHospitalsAPI(request: {
  location: string;
  specialization?: string;
  max_distance_km?: number;
  max_cost?: number;
  min_rating?: number;
  limit?: number;
}): Promise<Hospital[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}/hospitals/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        location: request.location,
        specialization: request.specialization,
        max_distance_km: request.max_distance_km ?? 50,
        max_cost: request.max_cost,
        min_rating: request.min_rating ?? 3.0,
        limit: request.limit ?? 10,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Hospital search API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to search hospitals: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Get hospitals near a specific location
 */
export async function getHospitalsNearLocationAPI(
  location: string,
  options?: {
    specialization?: string;
    max_distance?: number;
    max_cost?: number;
    min_rating?: number;
    limit?: number;
  }
): Promise<Hospital[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  const params = new URLSearchParams();
  if (options?.specialization) params.append('specialization', options.specialization);
  if (options?.max_distance) params.append('max_distance', options.max_distance.toString());
  if (options?.max_cost) params.append('max_cost', options.max_cost.toString());
  if (options?.min_rating) params.append('min_rating', options.min_rating.toString());
  if (options?.limit) params.append('limit', options.limit.toString());

  try {
    const response = await fetch(
      `${API_BASE_URL}/hospitals/near/${encodeURIComponent(location)}?${params}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Hospital location API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to get nearby hospitals: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Transform backend triage response to frontend SearchData format
 */
export function transformTriageToSearchData(
  triageResponse: Awaited<ReturnType<typeof callTriageAPI>>,
  hospitals: Hospital[],
  query: string,
  location: string
): SearchData {
  // Map severity to confidence score
  const severityConfidence: Record<string, number> = {
    'Red': 0.9,
    'Yellow': 0.75,
    'Green': 0.8,
  };

  const confidence = severityConfidence[triageResponse.severity] ?? 0.75;

  // Build cost range from cost estimate if available
  const costRange = triageResponse.cost_estimate
    ? {
        min: Math.round(triageResponse.cost_estimate.base_cost * 0.8),
        max: triageResponse.cost_estimate.adjusted_cost,
      }
    : { min: 50000, max: 200000 };

  // Get the first ICD-10 code for display
  const icd10Entries = Object.entries(triageResponse.icd10_codes);
  const primaryIcd10 = icd10Entries[0] ?? ['unknown', 'Unknown condition'];

  return {
    procedure: triageResponse.normalized_query,
    icd10_code: primaryIcd10[1],
    icd10_label: primaryIcd10[0],
    snomed_code: '',
    category: 'General Medicine',
    query_location: location,
    cost_range: costRange,
    confidence: confidence,
    cost_breakdown: triageResponse.cost_estimate?.breakdown
      ? Object.entries(triageResponse.cost_estimate.breakdown).reduce((acc, [key, value]) => {
          acc[key] = { min: Math.round(value * 0.9), max: value };
          return acc;
        }, {} as Record<string, { min: number; max: number }>)
      : undefined,
    comorbidity_warnings: [],
    hospitals: hospitals.slice(0, 3),
    clinical_mapping: {
      user_query: query,
      procedure: triageResponse.normalized_query,
      icd10_code: primaryIcd10[1],
      icd10_label: primaryIcd10[0],
      snomed_code: '',
      category: 'General Medicine',
      pathway: [],
      confidence: confidence,
      confidence_factors: [
        { key: 'severity_assessment', label: 'Severity Assessment', score: 85, weight: 0.4, note: triageResponse.rationale },
        { key: 'icd10_mapping', label: 'ICD-10 Mapping', score: 75, weight: 0.3, note: `Mapped to ${primaryIcd10[1]}` },
        { key: 'llm_confidence', label: 'AI Analysis', score: 80, weight: 0.3, note: 'Processed by NVIDIA Mistral LLM' },
      ],
    },
    pathway: [],
    confidence_factors: [],
    geo_adjustment: {
      city_tier: 'tier2',
      city_name: location,
      discount_vs_metro: 0.32,
    },
    tier_comparison: {
      budget: { min: Math.round(costRange.min * 0.7), max: Math.round(costRange.max * 0.6) },
      mid: { min: costRange.min, max: costRange.max },
      premium: { min: Math.round(costRange.min * 1.3), max: Math.round(costRange.max * 1.5) },
    },
    risk_adjustments: [],
    data_sources: [
      'NVIDIA Mistral LLM Analysis',
      'ICD-10 Medical Classification',
      'Healthcare Cost Database',
    ],
  };
}

// ============================================================================
// NEW API FUNCTIONS - Per instructionagent.md Section 6
// ============================================================================

/**
 * Master Orchestrator Chat API - POST /api/chat
 * Per instructionagent.md Section 6.1
 */
export async function callChatAPI(
  message: string,
  sessionId: string,
  location?: string,
  patientProfile?: {
    age?: number;
    comorbidities?: string[];
    budget_inr?: number;
    insurance?: boolean;
  }
): Promise<{
  session_id: string;
  chat_response: {
    message: string;
    triage: 'RED' | 'YELLOW' | 'GREEN';
    confidence_score: number;
    disclaimer: string;
  };
  clinical_interpretation?: {
    canonical_procedure: string;
    category: string;
    icd10: string;
    snomed_ct: string;
    mapping_confidence: number;
  };
  treatment_pathway?: {
    phases: Array<{
      phase: string;
      description: string;
      cost_range: { min: number; max: number };
    }>;
    total_estimated_cost: { min: number; max: number };
    comorbidity_note?: string;
  };
  cost_estimate?: {
    total: { min: number; max: number };
    components: Record<string, { min: number; max: number }>;
  };
  hospitals?: Hospital[];
  map_data?: {
    hospital_markers: Array<{
      id: string;
      lat: number;
      lng: number;
      name: string;
      tier: string;
      color: string;
    }>;
    map_config: {
      center: { lat: number; lng: number };
      zoom: number;
      legend: string;
    };
  };
  financial_assistance?: {
    dti_ratio: number;
    risk_flag: string;
    emi_options: { '12_months': number; '24_months': number; '36_months': number };
    government_schemes: Array<{ name: string; eligibility: string; coverage_pct: string }>;
    lending_partners: Array<{ name: string; rate_range: string; max_tenure: number }>;
    call_to_action: string;
  };
  appointment_checklist?: {
    availability_proxy: { wait_time_display: string };
    documents: Array<{ name: string; required: boolean; description: string }>;
    questions: string[];
    forms: Array<{ form_id: string; name: string; download_url: string }>;
  };
  xai_explanation?: {
    shap_waterfall: {
      final_score: number;
      features: Array<{ name: string; value: number; contribution: number }>;
    };
    lime_highlights?: {
      highlighted_tokens: Array<{ text: string; weight: number }>;
    };
    confidence_score: number;
    confidence_verdict: string;
  };
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message.trim(),
        session_id: sessionId,
        location,
        patient_profile: patientProfile,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Chat API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to call chat API: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Get Session State - GET /api/session/{session_id}
 * Per instructionagent.md Section 6.2
 */
export async function getSessionAPI(sessionId: string): Promise<{
  session_id: string;
  user_location?: {
    city: string;
    state?: string;
    lat?: number;
    lng?: number;
  };
  patient_profile?: {
    age?: number;
    comorbidities: string[];
    budget_inr?: number;
    insurance: boolean;
  };
  conversation_history: Array<{ role: string; content: string; timestamp?: string }>;
  last_procedure?: string;
  last_results?: Record<string, unknown>;
  saved_results: Array<Record<string, unknown>>;
  appointment_requests: Array<{
    appointment_id: string;
    hospital_name: string;
    procedure: string;
    status: 'requested' | 'confirmed' | 'cancelled';
    timestamp: string;
  }>;
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}/session/${encodeURIComponent(sessionId)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Session API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to get session: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Update Appointment Status - PATCH /api/session/{session_id}/appointment
 * Per instructionagent.md Section 6.3
 */
export async function updateAppointmentAPI(
  sessionId: string,
  appointmentId: string,
  status: 'requested' | 'confirmed' | 'cancelled'
): Promise<{
  success: boolean;
  appointment: {
    appointment_id: string;
    hospital_name: string;
    procedure: string;
    status: string;
    timestamp: string;
  };
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}/session/${encodeURIComponent(sessionId)}/appointment`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        appointment_id: appointmentId,
        status,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Appointment update API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to update appointment: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Calculate EMI - POST /api/emi-calculate
 * Per instructionagent.md Section 6.4
 */
export async function calculateEMIAPI(
  principal: number,
  annualRatePct: number,
  tenureMonths: number
): Promise<{
  monthly_emi: number;
  total_repayment: number;
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // Shorter timeout for EMI

  try {
    const response = await fetch(`${API_BASE_URL}/emi-calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        principal,
        annual_rate_pct: annualRatePct,
        tenure_months: tenureMonths,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `EMI API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to calculate EMI: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Submit Feedback - POST /api/feedback
 * Per instructionagent.md Section 6.5
 */
export async function submitFeedbackAPI(
  sessionId: string,
  originalQuery: string,
  mappedProcedure: string,
  userCorrection: string
): Promise<{
  success: boolean;
  message: string;
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(`${API_BASE_URL}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        original_query: originalQuery,
        mapped_procedure: mappedProcedure,
        user_correction: userCorrection,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Feedback API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to submit feedback: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Save Result - POST /api/save-result
 * Per instructionagent.md Section 6.6
 */
export async function saveResultAPI(
  sessionId: string,
  resultData: Record<string, unknown>
): Promise<{
  success: boolean;
  saved_count: number;
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(`${API_BASE_URL}/save-result`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        result_data: resultData,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Save result API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to save result: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Get Form Template - GET /api/form-template/{form_name}
 * Per instructionagent.md Section 6.7
 */
export async function getFormTemplateAPI(formName: string): Promise<Blob> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(`${API_BASE_URL}/form-template/${encodeURIComponent(formName)}`, {
      method: 'GET',
      headers: {
        'Accept': 'text/plain,application/pdf',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Form template API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.blob();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to get form template: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Lender Underwrite - POST /api/lender/underwrite
 * Per instructionagent.md Section 7
 */
export async function lenderUnderwriteAPI(request: {
  procedure: string;
  city: string;
  patient_income_monthly: number;
  existing_emis: number;
  loan_amount_requested: number;
  tenure_months: number;
}): Promise<{
  procedure: string;
  city: string;
  dti_assessment: {
    risk_level: string;
    rate_range: string;
    cta: string;
    dti_percentage: number;
  };
  tier_distribution: Array<{
    tier: string;
    hospital_count: number;
    avg_cost_min: number;
    avg_cost_max: number;
  }>;
  shap_attribution: {
    features: Array<{ feature: string; importance: number; impact: string }>;
    base_risk_score: number;
    final_risk_score: number;
    explanation: string;
  };
  recommendation: string;
}> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}/lender/underwrite`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new APIError(
        `Lender underwrite API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new APIError('Request timed out. The backend took too long to respond. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Backend is unreachable. Please ensure the backend server is running.');
    }

    throw new APIError(`Failed to get lender underwrite: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Create WebSocket Connection for Streaming Chat
 * Per instructionagent.md Section 12 - WebSocket
 */
export function createChatWebSocket(
  sessionId: string,
  onMessage: (data: { type: string; content?: string; full_response?: string }) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): WebSocket {
  // Determine WebSocket URL based on API_BASE_URL
  const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
  const wsHost = API_BASE_URL.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '');
  const wsUrl = `${wsProtocol}://${wsHost}/ws/chat/${encodeURIComponent(sessionId)}`;

  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected for session:', sessionId);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    onError?.(error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected for session:', sessionId);
    onClose?.();
  };

  return ws;
}

/**
 * Send chat message via WebSocket
 */
export function sendChatMessageViaWebSocket(
  ws: WebSocket,
  message: string,
  location?: string,
  patientProfile?: Record<string, unknown>
): void {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'message',
      content: message,
      location,
      patient_profile: patientProfile,
    }));
  } else {
    console.error('WebSocket is not open. Ready state:', ws.readyState);
  }
}
