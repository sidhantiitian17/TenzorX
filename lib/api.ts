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
const REQUEST_TIMEOUT = 30000;

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
    const response = await fetch(`${API_BASE_URL}/triage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.trim(),
        patient_profile: patientProfile,
        financial_profile: financialProfile,
      }),
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
