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
  const exportForUnderwriting = () => {
    const payload = {
      generatedAt: new Date().toISOString(),
      patientProfile,
      procedure: profile.procedure,
      icd10Code: profile.icd10_code,
      riskLevel: profile.risk_level,
      baseEstimate: profile.base_estimate,
      comorbidityAdjustment: profile.comorbidity_adjustment,
      maxForeseeableCost: profile.max_foreseeable_cost,
      recommendedCover: profile.recommended_cover,
      confidence: confidenceToPercent(profile.confidence),
      riskFactors: profile.risk_factors,
      procedureRisk: profile.procedure_risk,
      procedureRiskDetail: profile.procedure_risk_detail,
      disclaimer: 'HealthNav is decision support only and not clinical advice.',
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `healthnav-underwriting-${profile.icd10_code.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const shareWithTeam = async () => {
    const text = [
      `Procedure: ${profile.procedure}`,
      `ICD-10: ${profile.icd10_code}`,
      `Base estimate: ${formatCostRangeFull(profile.base_estimate)}`,
      `Recommended cover: ${formatCostRangeFull(profile.recommended_cover)}`,
      `Confidence: ${confidenceToPercent(profile.confidence)}%`,
      'Decision support only.',
    ].join('\n');

    if (navigator.share) {
      await navigator.share({ title: 'HealthNav Underwriting Summary', text });
      return;
    }

    await navigator.clipboard.writeText(text);
  };

  return (
    <Card className="sticky top-24">
      <CardHeader>
        <CardTitle className="text-base">Lender / Insurer View</CardTitle>
        <p className="text-sm text-muted-foreground">
          Patient: {patientProfile?.age ?? 'N/A'}{patientProfile?.gender ? ` ${patientProfile.gender.charAt(0).toUpperCase()}` : ''} · {patientProfile?.location || 'Unknown location'}
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
        {profile.procedure_risk_detail && (
          <div className="rounded-md border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
            <p className="mb-2 font-medium text-foreground">Structured risk profile</p>
            <div className="space-y-1">
              <p>Mortality risk benchmark: {profile.procedure_risk_detail.mortality_risk}%</p>
              <p>ICU probability: {profile.procedure_risk_detail.icu_probability}%</p>
              <p>Avg. length of stay: {profile.procedure_risk_detail.avg_los_days} days</p>
              <p>Re-admission rate: {profile.procedure_risk_detail.readmission_rate}%</p>
            </div>
          </div>
        )}
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
          <Button size="sm" onClick={exportForUnderwriting}>Export for Underwriting</Button>
          <Button size="sm" variant="outline" onClick={shareWithTeam}>Share with Team</Button>
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
