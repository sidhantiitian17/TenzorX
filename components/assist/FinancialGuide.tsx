'use client';

import { useMemo, useState, type ChangeEvent } from 'react';
import { ExternalLink, Lightbulb } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { formatINRFull } from '@/lib/formatters';

interface FinancialGuideProps {
  personalizedAdvice?: string;
  recommendedScheme?: string;
  dtiAssessment?: {
    risk_level: string;
    rate_range: string;
    cta: string;
  };
  costEstimate?: {
    min: number;
    max: number;
  };
}

function emi(principal: number, annualRate: number, months: number): number {
  const monthlyRate = annualRate / 12 / 100;
  if (monthlyRate === 0) return principal / months;
  return (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
}

export function FinancialGuide({
  personalizedAdvice,
  recommendedScheme,
  dtiAssessment,
  costEstimate,
}: FinancialGuideProps) {
  const [amount, setAmount] = useState(costEstimate?.min || 200000);
  const [rate, setRate] = useState(12.5);
  const [months, setMonths] = useState('24');
  const monthly = useMemo(() => emi(amount, rate, Number(months)), [amount, months, rate]);
  const totalPayment = useMemo(() => monthly * Number(months), [monthly, months]);

  const schemeLinks = [
    { 
      name: 'Ayushman Bharat PM-JAY', 
      url: 'https://pmjay.gov.in/', 
      description: 'Up to Rs 5L/year for eligible families.',
      isRecommended: recommendedScheme === 'Ayushman Bharat PM-JAY'
    },
    { 
      name: 'National Health Authority', 
      url: 'https://nha.gov.in/', 
      description: 'Scheme enrollment and beneficiary details.',
      isRecommended: recommendedScheme === 'National Health Authority'
    },
    { 
      name: 'State Health Scheme Portal', 
      url: 'https://www.india.gov.in/topics/health-family-welfare', 
      description: 'State-specific health assistance programs.',
      isRecommended: recommendedScheme === 'State Health Scheme Portal'
    },
  ];

  const loanOptions = [
    { name: 'Tata Capital Health Loan', range: 'Rs 50K - Rs 5L', approval: '24-72 hrs' },
    { name: 'Bajaj Finserv Health EMI', range: 'Rs 30K - Rs 7L', approval: 'Same day' },
    { name: 'HDFC Bank Medical Loan', range: 'Rs 1L - Rs 10L', approval: '1-3 days' },
  ];

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/30 p-4">
      <p className="text-sm font-semibold text-slate-100">Financial Assistance Guide</p>

      {/* AI-Personalized Financial Advice */}
      {personalizedAdvice && (
        <div className="mt-3 rounded-lg border border-teal-500/30 bg-teal-500/10 p-3">
          <div className="flex items-start gap-2">
            <Lightbulb className="h-4 w-4 text-teal-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-medium text-teal-300 mb-1">AI Financial Recommendation</p>
              <p className="text-xs text-teal-200">{personalizedAdvice}</p>
            </div>
          </div>
        </div>
      )}

      {/* DTI Assessment */}
      {dtiAssessment && (
        <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/50 p-3">
          <p className="text-xs font-medium text-slate-300 mb-1">Loan Eligibility Assessment</p>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Risk Level:</span>
            <span className={`font-medium ${
              dtiAssessment.risk_level === 'Low' ? 'text-emerald-400' :
              dtiAssessment.risk_level === 'Medium' ? 'text-yellow-400' :
              dtiAssessment.risk_level === 'High' ? 'text-orange-400' : 'text-red-400'
            }`}>
              {dtiAssessment.risk_level}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="text-slate-400">Interest Rate Range:</span>
            <span className="font-mono text-slate-400">{dtiAssessment.rate_range}</span>
          </div>
          <p className="text-xs text-slate-500 mt-2 italic">{dtiAssessment.cta}</p>
        </div>
      )}

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/50 p-3">
        <p className="text-sm font-medium text-slate-100">Government Schemes</p>
        <div className="mt-2 space-y-2 text-sm text-slate-400">
          {schemeLinks.map((scheme) => (
            <a
              key={scheme.name}
              href={scheme.url}
              target="_blank"
              rel="noreferrer"
              className={`block rounded-md border px-3 py-2 hover:bg-slate-800 ${
                scheme.isRecommended ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-slate-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="inline-flex items-center gap-1 font-medium text-slate-200">
                  {scheme.name}
                  {scheme.isRecommended && <span className="text-xs bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/30">Recommended</span>}
                  <ExternalLink className="h-3.5 w-3.5" />
                </p>
              </div>
              <p className="text-xs mt-1 text-slate-400">{scheme.description}</p>
            </a>
          ))}
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/50 p-3">
        <p className="text-sm font-medium text-slate-100">Healthcare Loan Options</p>
        <div className="mt-2 space-y-2 text-xs text-slate-400">
          {loanOptions.map((loan) => (
            <div key={loan.name} className="grid grid-cols-3 gap-2 rounded-md border border-slate-700 bg-slate-800/50 px-3 py-2">
              <span className="font-medium text-slate-200">{loan.name}</span>
              <span>{loan.range}</span>
              <span>{loan.approval}</span>
            </div>
          ))}
        </div>
      </div>

      <p className="mt-4 text-sm font-medium text-slate-100">EMI Calculator</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <Label className="text-slate-400">Loan amount</Label>
          <Input
            type="number"
            value={amount}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setAmount(Number(e.target.value) || 0)}
            className="bg-slate-900 border-slate-700 text-slate-100"
          />
        </div>
        <div>
          <Label className="text-slate-400">Interest rate (%)</Label>
          <Input
            type="number"
            min={0}
            step={0.1}
            value={rate}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setRate(Number(e.target.value) || 0)}
            className="bg-slate-900 border-slate-700 text-slate-100"
          />
        </div>
        <div>
          <Label className="text-slate-400">Tenure</Label>
          <Select value={months} onValueChange={setMonths}>
            <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-100">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="12" className="text-slate-300 focus:bg-slate-700">12 months</SelectItem>
              <SelectItem value="24" className="text-slate-300 focus:bg-slate-700">24 months</SelectItem>
              <SelectItem value="36" className="text-slate-300 focus:bg-slate-700">36 months</SelectItem>
              <SelectItem value="48" className="text-slate-300 focus:bg-slate-700">48 months</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-300">
        Estimated monthly EMI: <span className="font-semibold text-slate-100">{formatINRFull(Math.round(monthly))}</span>
      </p>
      <p className="mt-1 text-sm text-slate-400">
        Total repayment: {formatINRFull(Math.round(totalPayment))}
      </p>
      <p className="mt-1 text-xs text-slate-500">These are indicative figures. Confirm final rates with lenders.</p>
    </div>
  );
}
