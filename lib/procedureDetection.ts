/**
 * Real-time Procedure Detection Utility
 * 
 * Frontend utility for detecting medical procedures using the backend API.
 * Includes LRU cache with TTL to avoid repeated API calls for similar queries.
 */

import { ClinicalMapping } from '@/types';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const API_TIMEOUT = 10000; // 10 seconds

// Cache Configuration
const CACHE_MAX_SIZE = 100;
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

interface CacheEntry {
  result: ClinicalMapping;
  timestamp: number;
}

interface ProcedureDetectionResponse {
  success: boolean;
  data: {
    procedure: string;
    category: string;
    icd10_code: string;
    icd10_label: string;
    snomed_code: string;
    confidence: number;
    confidence_factors: Array<{
      key: string;
      label: string;
      score: number;
    }>;
    rationale: string;
  };
  query: string;
}

// In-memory cache
const cache = new Map<string, CacheEntry>();

/**
 * Normalize query string for cache key generation
 * - Lowercase
 * - Remove stopwords
 * - Sort keywords alphabetically
 */
function normalizeQuery(query: string): string {
  const stopwords = new Set([
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
    'your', 'yours', 'yourself', 'he', 'him', 'his', 'himself', 'she',
    'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
    'this', 'that', 'these', 'those', 'am', 'so', 'up', 'out', 'if',
    'about', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just', 'tell',
    'me', 'nearby', 'suggest', 'options', 'treatment', 'hospital'
  ]);

  return query
    .toLowerCase()
    .replace(/[^\w\s]/g, '') // Remove punctuation
    .split(/\s+/)
    .filter(word => word.length > 2 && !stopwords.has(word))
    .sort()
    .join(' ');
}

/**
 * Check if cache entry is still valid
 */
function isCacheValid(entry: CacheEntry): boolean {
  const now = Date.now();
  return (now - entry.timestamp) < CACHE_TTL_MS;
}

/**
 * Clean up old cache entries if cache is full
 * Removes oldest entries first (LRU-style)
 */
function cleanupCache(): void {
  if (cache.size < CACHE_MAX_SIZE) return;

  // Sort by timestamp and remove oldest 20%
  const entries = Array.from(cache.entries());
  entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
  
  const toRemove = Math.floor(CACHE_MAX_SIZE * 0.2);
  for (let i = 0; i < toRemove; i++) {
    cache.delete(entries[i][0]);
  }
}

/**
 * Get cached result if available and valid
 */
export function getCachedResult(query: string): ClinicalMapping | null {
  const cacheKey = normalizeQuery(query);
  const entry = cache.get(cacheKey);

  if (!entry) return null;
  if (!isCacheValid(entry)) {
    cache.delete(cacheKey);
    return null;
  }

  return entry.result;
}

/**
 * Store result in cache
 */
export function setCachedResult(query: string, result: ClinicalMapping): void {
  cleanupCache();
  const cacheKey = normalizeQuery(query);
  cache.set(cacheKey, {
    result,
    timestamp: Date.now(),
  });
}

/**
 * Clear the entire cache
 */
export function clearProcedureCache(): void {
  cache.clear();
}

/**
 * Get cache statistics
 */
export function getCacheStats(): { size: number; maxSize: number; ttlMs: number } {
  return {
    size: cache.size,
    maxSize: CACHE_MAX_SIZE,
    ttlMs: CACHE_TTL_MS,
  };
}

/**
 * Detect procedure from user query using backend API
 * Checks cache first, then makes API call if needed
 * 
 * @param query - User's health query
 * @returns Clinical mapping with procedure, ICD-10, SNOMED, category
 */
export async function detectProcedureRealtime(
  query: string
): Promise<ClinicalMapping | null> {
  if (!query || !query.trim()) {
    return null;
  }

  const trimmedQuery = query.trim();

  // Check cache first
  const cached = getCachedResult(trimmedQuery);
  if (cached) {
    console.log('[ProcedureDetection] Cache hit for query:', trimmedQuery.substring(0, 30));
    return cached;
  }

  try {
    console.log('[ProcedureDetection] API call for query:', trimmedQuery.substring(0, 30));
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    const response = await fetch(`${API_BASE_URL}/api/detect-procedure`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: trimmedQuery }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const data: ProcedureDetectionResponse = await response.json();

    if (!data.success || !data.data) {
      throw new Error('Invalid response from procedure detection API');
    }

    // Convert to ClinicalMapping format
    const clinicalMapping: ClinicalMapping = {
      user_query: trimmedQuery,
      procedure: data.data.procedure,
      icd10_code: data.data.icd10_code,
      icd10_label: data.data.icd10_label,
      snomed_code: data.data.snomed_code,
      category: data.data.category,
      pathway: [], // Pathway will be determined by mock data or other logic
      confidence: data.data.confidence,
      confidence_factors: data.data.confidence_factors.map((factor, index) => ({
        key: index === 0 ? 'severity_assessment' : 'llm_confidence',
        label: factor.label,
        score: factor.score,
        weight: 0.25,
        note: data.data.rationale,
      })),
    };

    // Store in cache
    setCachedResult(trimmedQuery, clinicalMapping);

    return clinicalMapping;
  } catch (error) {
    console.error('[ProcedureDetection] Error:', error);
    return null;
  }
}

/**
 * Detect procedure with fallback to default
 * Returns default mapping if detection fails
 * 
 * @param query - User's health query
 * @returns Clinical mapping (never null, has default fallback)
 */
export async function detectProcedureWithFallback(
  query: string
): Promise<ClinicalMapping> {
  const result = await detectProcedureRealtime(query);
  
  if (result) {
    return result;
  }

  // Return default mapping
  return {
    user_query: query || '',
    procedure: 'Medical Consultation',
    icd10_code: 'Z71.9',
    icd10_label: 'Person encountering health services in unspecified circumstances',
    snomed_code: '185424001',
    category: 'General Medicine',
    pathway: [],
    confidence: 0.3,
    confidence_factors: [
      {
        key: 'data_availability',
        label: 'Detection API unavailable',
        score: 30,
        weight: 1.0,
        note: 'Using default fallback due to detection failure',
      },
    ],
  };
}

/**
 * Batch detect procedures for multiple queries
 * Useful for comparing or processing multiple queries
 * 
 * @param queries - Array of user queries
 * @returns Array of clinical mappings
 */
export async function batchDetectProcedures(
  queries: string[]
): Promise<ClinicalMapping[]> {
  const promises = queries.map(q => detectProcedureWithFallback(q));
  return Promise.all(promises);
}
