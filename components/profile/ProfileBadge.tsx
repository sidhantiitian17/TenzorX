'use client';

import { User, MapPin } from 'lucide-react';
import type { PatientProfile } from '@/types';
import { formatINRShort } from '@/lib/formatters';

interface ProfileBadgeProps {
  profile: PatientProfile;
}

export function ProfileBadge({ profile }: ProfileBadgeProps) {
  const hasDetails = profile.age || profile.gender || profile.comorbidities.length > 0 || profile.location;
  const hasBudgetSet = profile.budget_min > 0 || profile.budget_max < 2000000;

  if (!hasDetails && !hasBudgetSet) {
    return null;
  }

  const parts: string[] = [];
  
  if (profile.location) {
    parts.push(profile.location);
  }
  if (profile.age) {
    parts.push(`${profile.age}y`);
  }
  if (profile.gender && profile.gender !== 'prefer_not_to_say') {
    parts.push(profile.gender.charAt(0).toUpperCase());
  }
  if (profile.comorbidities.length > 0) {
    parts.push(`${profile.comorbidities.length} conditions`);
  }

  const genderLabel = profile.gender && profile.gender !== 'prefer_not_to_say' ? profile.gender.charAt(0).toUpperCase() : null;
  const comorbidities = profile.comorbidities.slice(0, 2).join(', ');

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1.5 text-xs text-muted-foreground">
      <User className="h-3.5 w-3.5" />
      <span className="font-medium text-foreground">
        {profile.age ?? 'N/A'}{genderLabel ?? ''} · {profile.location || 'Unknown'} · {formatINRShort(profile.budget_max)} budget
      </span>
      {comorbidities && <span className="hidden md:inline">· {comorbidities}</span>}
      <MapPin className="h-3.5 w-3.5" />
    </div>
  );
}
