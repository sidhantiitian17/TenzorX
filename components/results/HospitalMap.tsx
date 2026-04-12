'use client';

import { useState, useCallback, useMemo } from 'react';
import {
  APIProvider,
  Map,
  AdvancedMarker,
  InfoWindow,
  useMap,
} from '@vis.gl/react-google-maps';
import { MapPin, Star, Navigation, Building2, X } from 'lucide-react';
import type { Hospital } from '@/types';
import { formatINR } from '@/lib/formatters';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface HospitalMapProps {
  hospitals: Hospital[];
  selectedHospitalId?: string;
  onHospitalSelect?: (hospitalId: string) => void;
  className?: string;
}

// Custom marker component
function HospitalMarker({
  hospital,
  isSelected,
  onClick,
}: {
  hospital: Hospital;
  isSelected: boolean;
  onClick: () => void;
}) {
  const tierColors = {
    premium: 'bg-primary text-primary-foreground',
    mid: 'bg-accent text-accent-foreground',
    budget: 'bg-emerald-600 text-white',
  };

  return (
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
          tierColors[hospital.tier]
        )}
      >
        <Building2 className="h-5 w-5" />
      </div>
      {isSelected && (
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 rotate-45 bg-primary border-r border-b border-white" />
      )}
    </button>
  );
}

// Info window content component
function HospitalInfoContent({
  hospital,
  onClose,
  onGetDirections,
}: {
  hospital: Hospital;
  onClose: () => void;
  onGetDirections: () => void;
}) {
  const tierLabels = {
    premium: 'Premium',
    mid: 'Mid-range',
    budget: 'Budget',
  };

  const tierColors = {
    premium: 'bg-primary/10 text-primary border-primary/20',
    mid: 'bg-accent/10 text-accent border-accent/20',
    budget: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
  };

  return (
    <div className="p-3 min-w-[280px] max-w-[320px]">
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
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1 text-xs h-8"
          onClick={onGetDirections}
        >
          <Navigation className="h-3.5 w-3.5 mr-1.5" />
          Directions
        </Button>
      </div>
    </div>
  );
}

// Map bounds controller
function MapBoundsController({ hospitals }: { hospitals: Hospital[] }) {
  const map = useMap();

  useMemo(() => {
    if (!map || hospitals.length === 0) return;

    const bounds = new google.maps.LatLngBounds();
    hospitals.forEach((hospital) => {
      bounds.extend({
        lat: hospital.coordinates.lat,
        lng: hospital.coordinates.lng,
      });
    });

    // Add some padding to the bounds
    map.fitBounds(bounds, { top: 50, right: 50, bottom: 50, left: 50 });
  }, [map, hospitals]);

  return null;
}

export function HospitalMap({
  hospitals,
  selectedHospitalId,
  onHospitalSelect,
  className,
}: HospitalMapProps) {
  const [activeInfoWindow, setActiveInfoWindow] = useState<string | null>(null);
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  // Calculate center based on all hospitals
  const center = useMemo(() => {
    if (hospitals.length === 0) {
      // Default to central India
      return { lat: 21.1458, lng: 79.0882 };
    }

    const sumLat = hospitals.reduce((sum, h) => sum + h.coordinates.lat, 0);
    const sumLng = hospitals.reduce((sum, h) => sum + h.coordinates.lng, 0);

    return {
      lat: sumLat / hospitals.length,
      lng: sumLng / hospitals.length,
    };
  }, [hospitals]);

  const handleMarkerClick = useCallback((hospitalId: string) => {
    setActiveInfoWindow(hospitalId);
    onHospitalSelect?.(hospitalId);
  }, [onHospitalSelect]);

  const handleGetDirections = useCallback((hospital: Hospital) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${hospital.coordinates.lat},${hospital.coordinates.lng}&destination_place_id=${encodeURIComponent(hospital.name)}`;
    window.open(url, '_blank');
  }, []);

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

  if (hospitals.length === 0) {
    return (
      <div className={cn('flex items-center justify-center bg-muted rounded-lg', className)}>
        <div className="text-center p-4">
          <MapPin className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            No hospitals to display on map
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('rounded-lg overflow-hidden border border-border', className)}>
      <APIProvider apiKey={apiKey}>
        <Map
          defaultCenter={center}
          defaultZoom={8}
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
          <MapBoundsController hospitals={hospitals} />
          
          {hospitals.map((hospital) => (
            <AdvancedMarker
              key={hospital.id}
              position={{
                lat: hospital.coordinates.lat,
                lng: hospital.coordinates.lng,
              }}
              onClick={() => handleMarkerClick(hospital.id)}
            >
              <HospitalMarker
                hospital={hospital}
                isSelected={selectedHospitalId === hospital.id || activeInfoWindow === hospital.id}
                onClick={() => handleMarkerClick(hospital.id)}
              />
            </AdvancedMarker>
          ))}

          {activeInfoWindow && (
            <InfoWindow
              position={{
                lat: hospitals.find((h) => h.id === activeInfoWindow)?.coordinates.lat || 0,
                lng: hospitals.find((h) => h.id === activeInfoWindow)?.coordinates.lng || 0,
              }}
              onCloseClick={() => setActiveInfoWindow(null)}
              pixelOffset={[0, -45]}
            >
              {hospitals.find((h) => h.id === activeInfoWindow) && (
                <HospitalInfoContent
                  hospital={hospitals.find((h) => h.id === activeInfoWindow)!}
                  onClose={() => setActiveInfoWindow(null)}
                  onGetDirections={() =>
                    handleGetDirections(hospitals.find((h) => h.id === activeInfoWindow)!)
                  }
                />
              )}
            </InfoWindow>
          )}
        </Map>
      </APIProvider>

      {/* Map Legend */}
      <div className="absolute bottom-3 left-3 bg-background/95 backdrop-blur-sm rounded-md p-2 shadow-md border border-border">
        <p className="text-xs font-medium text-foreground mb-1.5">Hospital Tier</p>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-primary" />
            <span className="text-xs text-muted-foreground">Premium</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-accent" />
            <span className="text-xs text-muted-foreground">Mid-range</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-emerald-600" />
            <span className="text-xs text-muted-foreground">Budget</span>
          </div>
        </div>
      </div>
    </div>
  );
}
