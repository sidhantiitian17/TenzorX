'use client';

import type { LenderRiskProfile, PatientProfile } from '@/types';
import { formatCostRangeFull, confidenceToPercent } from '@/lib/formatters';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface LenderDashboardProps {
  profile: LenderRiskProfile;
  patientProfile: PatientProfile | null;
}

export function LenderDashboard({ profile, patientProfile }: LenderDashboardProps) {
  return (
    <Card className="sticky top-24">
      <CardHeader>
        <CardTitle className="text-base">Lender / Insurer View</CardTitle>
        <p className="text-sm text-muted-foreground">
          Patient: {patientProfile?.age ?? 'N/A'} · {patientProfile?.location || 'Unknown location'}
        </p>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <Row label="Procedure" value={profile.procedure} />
        <Row label="ICD-10" value={profile.icd10_code} />
        <Row label="Risk Level" value={profile.risk_level} />
        <hr />
        <Row label="Base Estimate" value={formatCostRangeFull(profile.base_estimate)} />
        <Row label="Comorbidity Adjustment" value={`+ ${formatCostRangeFull(profile.comorbidity_adjustment)}`} />
        <Row label="Maximum Foreseeable" value={formatCostRangeFull(profile.max_foreseeable_cost)} />
        <Row label="Recommended Cover" value={formatCostRangeFull(profile.recommended_cover)} />
        <Row label="Confidence" value={`${confidenceToPercent(profile.confidence)}%`} />
        <hr />
        <div>
          <p className="mb-2 font-medium">Risk factors</p>
          <div className="space-y-2">
            {profile.risk_factors.map((risk) => (
              <div key={risk.factor} className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2">
                <span>{risk.factor}</span>
                <Badge variant="outline">{risk.severity}</Badge>
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <Button size="sm">Export for Underwriting</Button>
          <Button size="sm" variant="outline">Share with Team</Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-right">{value}</span>
    </div>
  );
}
