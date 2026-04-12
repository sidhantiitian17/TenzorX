'use client';

import { useMemo, useState, type ChangeEvent } from 'react';
import { ExternalLink } from 'lucide-react';
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
  const [rate, setRate] = useState(12.5);
  const [months, setMonths] = useState('24');
  const monthly = useMemo(() => emi(amount, rate, Number(months)), [amount, months, rate]);
  const totalPayment = useMemo(() => monthly * Number(months), [monthly, months]);

  const schemeLinks = [
    { name: 'Ayushman Bharat PM-JAY', url: 'https://pmjay.gov.in/', description: 'Up to Rs 5L/year for eligible families.' },
    { name: 'National Health Authority', url: 'https://nha.gov.in/', description: 'Scheme enrollment and beneficiary details.' },
    { name: 'State Health Scheme Portal', url: 'https://www.india.gov.in/topics/health-family-welfare', description: 'State-specific health assistance programs.' },
  ];

  const loanOptions = [
    { name: 'Tata Capital Health Loan', range: 'Rs 50K - Rs 5L', approval: '24-72 hrs' },
    { name: 'Bajaj Finserv Health EMI', range: 'Rs 30K - Rs 7L', approval: 'Same day' },
    { name: 'HDFC Bank Medical Loan', range: 'Rs 1L - Rs 10L', approval: '1-3 days' },
  ];

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-sm font-semibold">Financial Assistance Guide</p>

      <div className="mt-3 rounded-lg border border-border p-3">
        <p className="text-sm font-medium">Government Schemes</p>
        <div className="mt-2 space-y-2 text-sm text-muted-foreground">
          {schemeLinks.map((scheme) => (
            <a key={scheme.name} href={scheme.url} target="_blank" rel="noreferrer" className="block rounded-md border border-border px-3 py-2 hover:bg-muted/50">
              <p className="inline-flex items-center gap-1 font-medium text-foreground">
                {scheme.name}
                <ExternalLink className="h-3.5 w-3.5" />
              </p>
              <p className="text-xs">{scheme.description}</p>
            </a>
          ))}
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-border p-3">
        <p className="text-sm font-medium">Healthcare Loan Options</p>
        <div className="mt-2 space-y-2 text-xs text-muted-foreground">
          {loanOptions.map((loan) => (
            <div key={loan.name} className="grid grid-cols-3 gap-2 rounded-md border border-border px-3 py-2">
              <span className="font-medium text-foreground">{loan.name}</span>
              <span>{loan.range}</span>
              <span>{loan.approval}</span>
            </div>
          ))}
        </div>
      </div>

      <p className="mt-4 text-sm font-medium">EMI Calculator</p>
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
          <Label>Interest rate (%)</Label>
          <Input
            type="number"
            min={0}
            step={0.1}
            value={rate}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setRate(Number(e.target.value) || 0)}
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
      <p className="mt-1 text-sm text-muted-foreground">
        Total repayment: {formatINRFull(Math.round(totalPayment))}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">These are indicative figures. Confirm final rates with lenders.</p>
    </div>
  );
}
