'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import {
  APIProvider,
  Map,
  AdvancedMarker,
  InfoWindow,
  useMap,
} from '@vis.gl/react-google-maps';
import { MapPin, Star, Navigation, Building2, X, Locate, Layers } from 'lucide-react';
import type { Hospital } from '@/types';
import { formatINR } from '@/lib/formatters';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useAppState, useAppDispatch } from '@/lib/context';
import { 
  calculateDistance, 
  getDirectionsUrl,
  type Coordinates 
} from '@/lib/geoUtils';

interface HospitalMapProps {
  hospitals: Hospital[];
  selectedHospitalId?: string;
  onHospitalSelect?: (hospitalId: string) => void;
  className?: string;
  // Multi-source user location support
  userLocation?: Coordinates | null;
  searchLocation?: string;
  onDistanceUpdate?: (hospitals: Hospital[]) => void;
}

interface UserLocationData extends Coordinates {
  accuracy?: number;
  source: 'browser' | 'profile' | 'search';
}

// Permanent cost label marker with hospital info
function HospitalMarkerWithCost({
  hospital,
  isSelected,
  isTopRanked,
  onClick,
}: {
  hospital: Hospital;
  isSelected: boolean;
  isTopRanked: boolean;
  onClick: () => void;
}) {
  const tierColors = {
    premium: { bg: 'bg-blue-500', text: 'text-white', border: 'border-blue-400' },
    mid: { bg: 'bg-purple-500', text: 'text-white', border: 'border-purple-400' },
    budget: { bg: 'bg-emerald-500', text: 'text-white', border: 'border-emerald-400' },
  };

  const tier = tierColors[hospital.tier];

  // Format cost label (e.g., "1.5L" instead of "150000")
  const formatCostLabel = (amount: number): string => {
    if (amount >= 100000) {
      return `${(amount / 100000).toFixed(1)}L`.replace('.0L', 'L');
    }
    if (amount >= 1000) {
      return `${(amount / 1000).toFixed(0)}K`;
    }
    return `${amount}`;
  };

  const costMin = formatCostLabel(hospital.cost_range.min);
  const costMax = formatCostLabel(hospital.cost_range.max);
  const costLabel = `Rs ${costMin} – ${costMax}`;

  return (
    <div className="relative flex flex-col items-center">
      {/* Permanent Cost Label Above Marker */}
      <div
        className={cn(
          'mb-1 px-2 py-0.5 rounded-md shadow-md border text-xs font-semibold whitespace-nowrap backdrop-blur-sm',
          'bg-background/95 border-border text-foreground',
          'transition-all duration-200',
          isSelected ? 'scale-110 z-20' : 'hover:scale-105'
        )}
      >
        {costLabel}
      </div>
      
      {/* Distance Badge */}
      <div
        className={cn(
          'mb-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium whitespace-nowrap backdrop-blur-sm',
          hospital.distance_km < 3 
            ? 'bg-green-500/90 text-white' 
            : hospital.distance_km < 7 
              ? 'bg-blue-500/90 text-white' 
              : 'bg-gray-500/80 text-white',
          'transition-all duration-200',
          isSelected ? 'scale-105 z-20' : ''
        )}
      >
        {hospital.distance_km < 1 ? '< 1 km' : `${hospital.distance_km.toFixed(1)} km`}
      </div>

      {/* Hospital Marker Button */}
      <button
        onClick={onClick}
        className={cn(
          'relative flex items-center justify-center transition-all duration-200',
          isSelected ? 'scale-125 z-10' : 'hover:scale-110'
        )}
        aria-label={`View ${hospital.name}`}
      >
        <div
          className={cn(
            'flex items-center justify-center w-10 h-10 rounded-full shadow-lg border-2 border-white',
            tier.bg,
            tier.text
          )}
        >
          <Building2 className="h-5 w-5" />
        </div>
        {isTopRanked && (
          <div className="absolute -top-2 -right-2 bg-yellow-400 text-yellow-900 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold shadow-md">
            1
          </div>
        )}
        {hospital.nabh_accredited && (
          <div className="absolute -bottom-1 -right-1 bg-teal-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-[8px] font-bold shadow-md">
            N
          </div>
        )}
      </button>
    </div>
  );
}

// User Location Marker with pulse effect
function UserLocationMarker({ location }: { location: UserLocationData }) {
  return (
    <div className="relative flex items-center justify-center">
      {/* Pulse rings */}
      <div className="absolute w-12 h-12 rounded-full bg-blue-500/30 animate-ping" />
      <div className="absolute w-8 h-8 rounded-full bg-blue-500/50 animate-pulse" />
      
      {/* Center dot */}
      <div className="relative w-4 h-4 rounded-full bg-blue-600 border-2 border-white shadow-lg z-10" />
    </div>
  );
}

// Map Legend with tier filtering
function MapLegend() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const tiers = [
    { key: 'premium', label: 'Premium', color: 'bg-blue-500' },
    { key: 'mid', label: 'Mid-range', color: 'bg-purple-500' },
    { key: 'budget', label: 'Budget', color: 'bg-emerald-500' },
  ] as const;

  return (
    <div className="absolute bottom-3 left-3 bg-background/95 backdrop-blur-sm rounded-lg p-3 shadow-md border border-border z-10">
      <div className="flex items-center gap-1.5 mb-2">
        <Layers className="h-3.5 w-3.5 text-muted-foreground" />
        <p className="text-xs font-medium text-foreground">Filter by Tier</p>
      </div>
      <div className="flex flex-col gap-1.5">
        {tiers.map((tier) => (
          <button
            key={tier.key}
            onClick={() => dispatch({ type: 'SET_FILTERS', payload: { tier: tier.key } })}
            className={cn(
              'flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-all',
              state.filters.tier === tier.key
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'hover:bg-muted text-muted-foreground'
            )}
          >
            <div className={cn('w-3 h-3 rounded-full', tier.color)} />
            <span>{tier.label}</span>
          </button>
        ))}
        <button
          onClick={() => dispatch({ type: 'SET_FILTERS', payload: { tier: 'all' } })}
          className={cn(
            'flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-all',
            state.filters.tier === 'all'
              ? 'bg-teal-500/10 text-teal-600 border border-teal-500/20'
              : 'hover:bg-muted text-muted-foreground'
          )}
        >
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-emerald-500" />
          <span>All Tiers</span>
        </button>
      </div>
    </div>
  );
}

// Map Controls
function MapControls({
  onGetUserLocation,
  userLocation,
  isLocating,
}: {
  onGetUserLocation: () => void;
  userLocation: UserLocationData | null;
  isLocating: boolean;
}) {
  return (
    <div className="absolute top-3 right-3 flex flex-col gap-2 z-10">
      <Button
        variant="secondary"
        size="icon"
        className={cn(
          'h-9 w-9 shadow-md border border-border bg-background/95 backdrop-blur-sm',
          isLocating && 'animate-pulse'
        )}
        onClick={onGetUserLocation}
        title={userLocation ? 'Update my location' : 'Get my location'}
      >
        <Locate className={cn('h-4 w-4', userLocation ? 'text-blue-500' : 'text-muted-foreground')} />
      </Button>
    </div>
  );
}

// Filtered hospitals based on global filter state
function useFilteredHospitals(hospitals: Hospital[]) {
  const state = useAppState();

  return useMemo(() => {
    let filtered = [...hospitals];

    // Filter by tier
    if (state.filters.tier !== 'all') {
      filtered = filtered.filter((h) => h.tier === state.filters.tier);
    }

    // Filter by NABH
    if (state.filters.nabhOnly) {
      filtered = filtered.filter((h) => h.nabh_accredited);
    }

    // Filter by rating
    if (state.filters.rating !== null) {
      filtered = filtered.filter((h) => h.rating >= state.filters.rating!);
    }

    // Filter by distance
    if (state.filters.distanceKm !== null) {
      const maxDistance = state.filters.distanceKm;
      filtered = filtered.filter((h) => h.distance_km <= maxDistance);
    }

    return filtered;
  }, [hospitals, state.filters]);
}

// Info window content component
function HospitalInfoContent({
  hospital,
  onClose,
  onGetDirections,
  userLocation,
}: {
  hospital: Hospital;
  onClose: () => void;
  onGetDirections: (fromUserLocation: boolean) => void;
  userLocation: UserLocationData | null;
}) {
  const tierLabels = {
    premium: 'Premium',
    mid: 'Mid-range',
    budget: 'Budget',
  };

  const tierColors = {
    premium: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
    mid: 'bg-purple-500/10 text-purple-600 border-purple-500/20',
    budget: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
  };

  return (
    <div className="p-3 min-w-72 max-w-80">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-foreground text-sm leading-tight">
            {hospital.name}
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {hospital.location}
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 shrink-0"
          onClick={onClose}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        <Badge variant="outline" className={cn('text-xs', tierColors[hospital.tier])}>
          {tierLabels[hospital.tier]}
        </Badge>
        {hospital.nabh_accredited && (
          <Badge variant="outline" className="text-xs bg-teal-500/10 text-teal-600 border-teal-500/20">
            NABH
          </Badge>
        )}
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
          <span>{hospital.rating.toFixed(1)}</span>
        </div>
        {hospital.distance_km > 0 && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="h-3 w-3" />
            <span>{hospital.distance_km.toFixed(1)} km</span>
          </div>
        )}
      </div>

      {/* Cost Range */}
      <div className="bg-muted/50 rounded-md p-2 mb-3">
        <p className="text-xs text-muted-foreground">Estimated Cost Range</p>
        <p className="font-semibold text-sm text-foreground">
          {formatINR(hospital.cost_range.min)} - {formatINR(hospital.cost_range.max)}
        </p>
      </div>

      {/* Specializations */}
      <div className="mb-3">
        <p className="text-xs text-muted-foreground mb-1">Specializations</p>
        <div className="flex flex-wrap gap-1">
          {hospital.specializations.slice(0, 3).map((spec) => (
            <span
              key={spec}
              className="text-xs bg-muted px-1.5 py-0.5 rounded text-muted-foreground"
            >
              {spec}
            </span>
          ))}
          {hospital.specializations.length > 3 && (
            <span className="text-xs text-muted-foreground">
              +{hospital.specializations.length - 3} more
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col gap-2">
        <Button
          variant="default"
          size="sm"
          className="flex-1 text-xs h-8 bg-blue-600 hover:bg-blue-700"
          onClick={() => onGetDirections(true)}
          disabled={!userLocation}
        >
          <Navigation className="h-3.5 w-3.5 mr-1.5" />
          {userLocation ? 'Directions from My Location' : 'Enable Location for Directions'}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="flex-1 text-xs h-8"
          onClick={() => onGetDirections(false)}
        >
          <MapPin className="h-3.5 w-3.5 mr-1.5" />
          View on Google Maps
        </Button>
      </div>
    </div>
  );
}

// Map bounds controller - includes both hospitals and user location
function MapBoundsController({
  hospitals,
  userLocation,
}: {
  hospitals: Hospital[];
  userLocation: UserLocationData | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || hospitals.length === 0) return;

    const bounds = new google.maps.LatLngBounds();

    // Add hospitals to bounds
    hospitals.forEach((hospital) => {
      bounds.extend({
        lat: hospital.coordinates.lat,
        lng: hospital.coordinates.lng,
      });
    });

    // Add user location to bounds if available
    if (userLocation) {
      bounds.extend({
        lat: userLocation.lat,
        lng: userLocation.lng,
      });
    }

    // Add some padding to the bounds
    map.fitBounds(bounds, { top: 80, right: 50, bottom: 50, left: 50 });
  }, [map, hospitals, userLocation]);

  return null;
}

export function HospitalMap({
  hospitals,
  selectedHospitalId,
  onHospitalSelect,
  className,
  onDistanceUpdate,
}: HospitalMapProps) {
  const [activeInfoWindow, setActiveInfoWindow] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<UserLocationData | null>(null);
  const [isLocating, setIsLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  // Get filtered hospitals based on global filter state
  const filteredHospitals = useFilteredHospitals(hospitals);
  
  // Calculate real-time distances from user's browser location to hospitals
  const hospitalsWithDistance = useMemo(() => {
    if (!userLocation || hospitals.length === 0) {
      return hospitals;
    }
    
    // Recalculate distances from user's actual GPS location
    const updated = hospitals.map(h => ({
      ...h,
      distance_km: calculateDistance(userLocation, h.coordinates),
    }));
    
    return updated;
  }, [hospitals, userLocation]);
  
  // Notify parent component of distance updates for sorting/filtering
  useEffect(() => {
    if (userLocation && onDistanceUpdate && hospitalsWithDistance.length > 0) {
      onDistanceUpdate(hospitalsWithDistance);
    }
  }, [hospitalsWithDistance, userLocation, onDistanceUpdate]);

  // Calculate center based on filtered hospitals and user location
  const center = useMemo(() => {
    if (filteredHospitals.length === 0 && !userLocation) {
      // Default to central India
      return { lat: 21.1458, lng: 79.0882 };
    }

    const points = [];
    filteredHospitals.forEach((h) => {
      points.push({ lat: h.coordinates.lat, lng: h.coordinates.lng });
    });
    if (userLocation) {
      points.push(userLocation);
    }

    const sumLat = points.reduce((sum, p) => sum + p.lat, 0);
    const sumLng = points.reduce((sum, p) => sum + p.lng, 0);

    return {
      lat: sumLat / points.length,
      lng: sumLng / points.length,
    };
  }, [filteredHospitals, userLocation]);

  // Get user's current location
  const getUserLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      return;
    }

    setIsLocating(true);
    setLocationError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy,
          source: 'browser',
        });
        setIsLocating(false);
      },
      (error) => {
        setIsLocating(false);
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError('Location permission denied. Please enable location access in your browser settings.');
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationError('Location information unavailable.');
            break;
          case error.TIMEOUT:
            setLocationError('Location request timed out.');
            break;
          default:
            setLocationError('An error occurred while getting your location.');
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }, []);

  // Get user location on component mount
  useEffect(() => {
    getUserLocation();
  }, [getUserLocation]);

  const handleMarkerClick = useCallback((hospitalId: string) => {
    setActiveInfoWindow(hospitalId);
    onHospitalSelect?.(hospitalId);
  }, [onHospitalSelect]);

  const handleGetDirections = useCallback((hospital: Hospital, fromUserLocation: boolean) => {
    let url: string;

    if (fromUserLocation && userLocation) {
      // Directions from user's current location
      url = `https://www.google.com/maps/dir/?api=1&origin=${userLocation.lat},${userLocation.lng}&destination=${hospital.coordinates.lat},${hospital.coordinates.lng}&destination_place_id=${encodeURIComponent(hospital.name)}`;
    } else {
      // Just open the hospital location on Google Maps
      url = `https://www.google.com/maps/search/?api=1&query=${hospital.coordinates.lat},${hospital.coordinates.lng}&query_place_id=${encodeURIComponent(hospital.name)}`;
    }

    window.open(url, '_blank');
  }, [userLocation]);

  if (!apiKey) {
    return (
      <div className={cn('flex items-center justify-center bg-muted rounded-lg', className)}>
        <div className="text-center p-6 max-w-sm">
          <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
          <h3 className="font-semibold text-foreground mb-2">Map Feature Ready</h3>
          <p className="text-sm text-muted-foreground mb-4">
            The map view will be available once configured. Switch to <strong>List View</strong> to browse hospitals.
          </p>
          <p className="text-xs text-muted-foreground italic">
            For admin: Add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to .env.local
          </p>
        </div>
      </div>
    );
  }

  if (filteredHospitals.length === 0) {
    return (
      <div className={cn('flex items-center justify-center bg-muted rounded-lg', className)}>
        <div className="text-center p-4">
          <MapPin className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            No hospitals match your current filters
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Try adjusting your tier, distance, or rating filters
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('relative rounded-lg overflow-hidden border border-border', className)}>
      <APIProvider apiKey={apiKey}>
        <Map
          defaultCenter={center}
          defaultZoom={13}
          mapId="healthnav-hospital-map"
          gestureHandling="greedy"
          disableDefaultUI={false}
          zoomControl={true}
          mapTypeControl={false}
          streetViewControl={false}
          fullscreenControl={true}
          className="w-full h-full"
          style={{ width: '100%', height: '100%' }}
        >
          <MapBoundsController hospitals={filteredHospitals} userLocation={userLocation} />

          {/* User Location Marker */}
          {userLocation && (
            <AdvancedMarker
              position={userLocation}
              title="Your Location"
            >
              <UserLocationMarker location={userLocation} />
            </AdvancedMarker>
          )}

          {/* Hospital Markers with Cost Labels */}
          {filteredHospitals.map((hospital, index) => (
            <AdvancedMarker
              key={hospital.id}
              position={{
                lat: hospital.coordinates.lat,
                lng: hospital.coordinates.lng,
              }}
              onClick={() => handleMarkerClick(hospital.id)}
            >
              <HospitalMarkerWithCost
                hospital={hospital}
                isSelected={selectedHospitalId === hospital.id || activeInfoWindow === hospital.id}
                isTopRanked={index === 0}
                onClick={() => handleMarkerClick(hospital.id)}
              />
            </AdvancedMarker>
          ))}

          {/* Active Info Window */}
          {activeInfoWindow && (
            <InfoWindow
              position={{
                lat: filteredHospitals.find((h) => h.id === activeInfoWindow)?.coordinates.lat || 0,
                lng: filteredHospitals.find((h) => h.id === activeInfoWindow)?.coordinates.lng || 0,
              }}
              onCloseClick={() => setActiveInfoWindow(null)}
              pixelOffset={[0, -60]}
            >
              {filteredHospitals.find((h) => h.id === activeInfoWindow) && (
                <HospitalInfoContent
                  hospital={filteredHospitals.find((h) => h.id === activeInfoWindow)!}
                  onClose={() => setActiveInfoWindow(null)}
                  onGetDirections={(fromUser) =>
                    handleGetDirections(filteredHospitals.find((h) => h.id === activeInfoWindow)!, fromUser)
                  }
                  userLocation={userLocation}
                />
              )}
            </InfoWindow>
          )}
        </Map>
      </APIProvider>

      {/* Map Controls - User Location */}
      <MapControls
        onGetUserLocation={getUserLocation}
        userLocation={userLocation}
        isLocating={isLocating}
      />

      {/* Map Legend with Tier Filtering */}
      <MapLegend />

      {/* Location Error Toast */}
      {locationError && (
        <div className="absolute top-3 left-3 right-3 bg-red-500/90 text-white px-3 py-2 rounded-md text-xs shadow-md z-20">
          {locationError}
          <button
            onClick={() => setLocationError(null)}
            className="ml-2 font-semibold hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
