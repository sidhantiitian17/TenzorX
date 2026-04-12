'use client';

import { useMemo, useState, type ChangeEvent } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { formatINRFull } from '@/lib/formatters';

function emi(principal: number, annualRate: number, months: number): number {
  const monthlyRate = annualRate / 12 / 100;
  if (monthlyRate === 0) return principal / months;
  return (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
}

export function FinancialGuide() {
  const [amount, setAmount] = useState(200000);
  const [months, setMonths] = useState('24');
  const monthly = useMemo(() => emi(amount, 12.5, Number(months)), [amount, months]);

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-sm font-semibold">Financial Assistance Guide</p>
      <div className="mt-3 space-y-2 text-sm text-muted-foreground">
        <p><span className="font-medium text-foreground">Government schemes:</span> Ayushman Bharat PM-JAY, state health support programs.</p>
        <p><span className="font-medium text-foreground">Healthcare loans:</span> Typical range Rs 50,000 to Rs 5,00,000, approval in 24 to 72 hours.</p>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <Label>Loan amount</Label>
          <Input
            type="number"
            value={amount}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setAmount(Number(e.target.value) || 0)}
          />
        </div>
        <div>
          <Label>Tenure</Label>
          <Select value={months} onValueChange={setMonths}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="12">12 months</SelectItem>
              <SelectItem value="24">24 months</SelectItem>
              <SelectItem value="36">36 months</SelectItem>
              <SelectItem value="48">48 months</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <p className="mt-3 text-sm">
        Estimated monthly EMI: <span className="font-semibold">{formatINRFull(Math.round(monthly))}</span>
      </p>
      <p className="mt-1 text-xs text-muted-foreground">These are indicative figures. Confirm final rates with lenders.</p>
    </div>
  );
}
