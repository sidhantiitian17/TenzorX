/**
 * Geographic utilities for distance calculation and location handling.
 * 
 * Provides Haversine formula for accurate distance calculation between
 * user location and hospitals. Supports multiple user location sources.
 */

import type { Hospital } from '@/types';

export interface Coordinates {
  lat: number;
  lng: number;
}

/**
 * Calculate distance between two points using Haversine formula.
 * More accurate than simple Euclidean distance for Earth's surface.
 * 
 * @param point1 - First coordinate (user location)
 * @param point2 - Second coordinate (hospital location)
 * @returns Distance in kilometers, rounded to 1 decimal place
 */
export function calculateDistance(point1: Coordinates, point2: Coordinates): number {
  const R = 6371; // Earth's radius in kilometers
  
  const lat1Rad = (point1.lat * Math.PI) / 180;
  const lat2Rad = (point2.lat * Math.PI) / 180;
  const deltaLatRad = ((point2.lat - point1.lat) * Math.PI) / 180;
  const deltaLngRad = ((point2.lng - point1.lng) * Math.PI) / 180;
  
  const a = 
    Math.sin(deltaLatRad / 2) * Math.sin(deltaLatRad / 2) +
    Math.cos(lat1Rad) * Math.cos(lat2Rad) *
    Math.sin(deltaLngRad / 2) * Math.sin(deltaLngRad / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  
  return Math.round(distance * 10) / 10; // Round to 1 decimal place
}

/**
 * Calculate distances from user location to all hospitals.
 * Updates each hospital's distance_km with actual calculated distance.
 * 
 * @param hospitals - Array of hospitals
 * @param userLocation - User's coordinates
 * @returns Hospitals with updated distance_km
 */
export function calculateHospitalDistances(
  hospitals: Hospital[],
  userLocation: Coordinates
): Hospital[] {
  return hospitals.map(hospital => ({
    ...hospital,
    distance_km: calculateDistance(userLocation, hospital.coordinates),
  }));
}

/**
 * Sort hospitals by distance from user location.
 * 
 * @param hospitals - Array of hospitals
 * @param userLocation - User's coordinates
 * @returns Sorted array (nearest first)
 */
export function sortHospitalsByDistance(
  hospitals: Hospital[],
  userLocation: Coordinates
): Hospital[] {
  const withDistances = calculateHospitalDistances(hospitals, userLocation);
  return withDistances.sort((a, b) => a.distance_km - b.distance_km);
}

/**
 * Filter hospitals by maximum distance from user.
 * 
 * @param hospitals - Array of hospitals
 * @param userLocation - User's coordinates
 * @param maxDistanceKm - Maximum distance in kilometers
 * @returns Filtered hospitals within range
 */
export function filterHospitalsByDistance(
  hospitals: Hospital[],
  userLocation: Coordinates,
  maxDistanceKm: number
): Hospital[] {
  const withDistances = calculateHospitalDistances(hospitals, userLocation);
  return withDistances.filter(h => h.distance_km <= maxDistanceKm);
}

/**
 * Get user's browser geolocation with promise-based API.
 * 
 * @returns Promise resolving to coordinates
 */
export function getBrowserLocation(): Promise<Coordinates> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by your browser'));
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      },
      (error) => {
        let message: string;
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message = 'Location permission denied';
            break;
          case error.POSITION_UNAVAILABLE:
            message = 'Location information unavailable';
            break;
          case error.TIMEOUT:
            message = 'Location request timed out';
            break;
          default:
            message = 'An error occurred while getting location';
        }
        reject(new Error(message));
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  });
}

/**
 * Format distance for display.
 * Shows "< 1 km" for very close, otherwise "X.X km".
 * 
 * @param distanceKm - Distance in kilometers
 * @returns Formatted string
 */
export function formatDistance(distanceKm: number): string {
  if (distanceKm < 1) {
    return '< 1 km';
  }
  return `${distanceKm.toFixed(1)} km`;
}

/**
 * Get distance category for UI badges.
 * 
 * @param distanceKm - Distance in kilometers
 * @returns Category label
 */
export function getDistanceCategory(distanceKm: number): 'very-close' | 'close' | 'moderate' | 'far' {
  if (distanceKm < 3) return 'very-close';
  if (distanceKm < 7) return 'close';
  if (distanceKm < 15) return 'moderate';
  return 'far';
}

/**
 * Generate Google Maps directions URL.
 * 
 * @param userLocation - Starting point
 * @param hospital - Destination hospital
 * @returns Google Maps URL
 */
export function getDirectionsUrl(userLocation: Coordinates, hospital: Hospital): string {
  const origin = `${userLocation.lat},${userLocation.lng}`;
  const destination = `${hospital.coordinates.lat},${hospital.coordinates.lng}`;
  return `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&destination_place_id=${encodeURIComponent(hospital.name)}`;
}

/**
 * Extract city name from a query string.
 * Looks for common Indian city names.
 * 
 * @param query - User query string
 * @returns City name or null if not found
 */
export function extractCityFromQuery(query: string): string | null {
  const cityPatterns = [
    /(?:in|at|near)\s+([a-zA-Z\s]+?)(?:\s+(?:for|with|under|hospital|clinic|$))/i,
    /([a-zA-Z]+(?:\s+nagar|\s+road|\s+hills|\s+west|\s+east)?)/i,
  ];
  
  const cities = [
    'bangalore', 'bengaluru', 'mumbai', 'bombay', 'delhi', 'new delhi',
    'hyderabad', 'chennai', 'madras', 'pune', 'ahmedabad', 'kolkata', 'calcutta',
    'nagpur', 'raipur', 'bhopal', 'indore', 'surat', 'patna', 'jaipur',
    'lucknow', 'kanpur', 'nashik', 'aurangabad', 'visakhapatnam', 'vadodara',
    'ludhiana', 'coimbatore', 'madurai', 'mangalore', 'mysore', 'trivandrum', 'kochi'
  ];
  
  const queryLower = query.toLowerCase();
  
  // Check for direct city mentions
  for (const city of cities) {
    if (queryLower.includes(city)) {
      // Normalize city names
      if (city === 'bengaluru') return 'Bangalore';
      if (city === 'bombay') return 'Mumbai';
      if (city === 'madras') return 'Chennai';
      if (city === 'calcutta') return 'Kolkata';
      return city.charAt(0).toUpperCase() + city.slice(1);
    }
  }
  
  return null;
}
