import type { CostRange } from '@/types';

export function formatINR(amount: number): string {
  return `Rs ${amount.toLocaleString('en-IN')}`;
}

export function formatINRShort(amount: number): string {
  if (amount >= 100000) {
    return `Rs ${(amount / 100000).toFixed(1)}L`;
  }
  if (amount >= 1000) {
    return `Rs ${(amount / 1000).toFixed(0)}K`;
  }
  return `Rs ${amount}`;
}

export function formatINRFull(amount: number): string {
  return `Rs ${amount.toLocaleString('en-IN')}`;
}

export function formatCostRange(range: CostRange): string {
  return `${formatINRShort(range.min)} – ${formatINRShort(range.max)}`;
}

export function formatCostRangeFull(range: CostRange): string {
  return `${formatINRFull(range.min)} – ${formatINRFull(range.max)}`;
}

export function formatDistance(km: number): string {
  if (km < 1) {
    return `${Math.round(km * 1000)}m`;
  }
  return `${km.toFixed(1)} km`;
}

export function formatRating(rating: number): string {
  return rating.toFixed(1);
}

export function getConfidenceLabel(confidence: number): 'Low' | 'Moderate' | 'High' {
  if (confidence < 0.4) return 'Low';
  if (confidence < 0.7) return 'Moderate';
  return 'High';
}

export function getConfidenceColor(confidence: number): string {
  if (confidence < 0.4) return 'text-red-500';
  if (confidence < 0.7) return 'text-amber-500';
  return 'text-emerald-500';
}

export function confidenceToPercent(confidence: number): number {
  return Math.max(0, Math.min(100, Math.round(confidence * 100)));
}

export function getTierLabel(tier: 'premium' | 'mid' | 'budget'): string {
  const labels = {
    premium: 'Premium',
    mid: 'Mid-tier',
    budget: 'Budget',
  };
  return labels[tier];
}

export function getTierColor(tier: 'premium' | 'mid' | 'budget'): string {
  const colors = {
    premium: 'bg-violet-100 text-violet-700',
    mid: 'bg-blue-100 text-blue-700',
    budget: 'bg-emerald-100 text-emerald-700',
  };
  return colors[tier];
}

export function formatTimestamp(date: Date): string {
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

export function extractSearchData(content: string): { text: string; searchData: object | null } {
  const searchDataMatch = content.match(/<SEARCH_DATA>([\s\S]*?)<\/SEARCH_DATA>/);
  
  if (searchDataMatch) {
    try {
      const searchData = JSON.parse(searchDataMatch[1]);
      const text = content.replace(/<SEARCH_DATA>[\s\S]*?<\/SEARCH_DATA>/, '').trim();
      return { text, searchData };
    } catch {
      return { text: content, searchData: null };
    }
  }
  
  return { text: content, searchData: null };
}

export function calculateBestValueScore(
  rating: number,
  costMidpoint: number,
  confidence: number
): number {
  const normalizedCost = costMidpoint > 0 ? 1 / costMidpoint : 0;
  return rating * 0.4 + normalizedCost * 100000 * 0.3 + confidence * 100 * 0.3;
}
