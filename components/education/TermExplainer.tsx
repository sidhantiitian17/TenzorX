'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export interface TermDefinition {
  term: string;
  simple: string;
  analogy: string;
  duration: string;
  stay: string;
  recovery: string;
  icd10: string;
  snomed: string;
}

const TERM_MAP: Record<string, TermDefinition> = {
  angioplasty: {
    term: 'Angioplasty',
    simple: 'A minimally invasive procedure to open narrowed heart blood vessels.',
    analogy: 'Like unclogging a pipe so blood can flow smoothly again.',
    duration: '30 to 90 minutes',
    stay: 'Usually 1 to 3 nights',
    recovery: 'About 1 to 2 weeks for light routine',
    icd10: 'I25.10',
    snomed: '418285008',
  },
  'knee replacement': {
    term: 'Knee Replacement',
    simple: 'A damaged knee joint is replaced with an artificial implant.',
    analogy: 'Replacing a worn hinge so the joint can move with less pain.',
    duration: '2 to 3 hours',
    stay: 'Typically 3 to 5 nights',
    recovery: '6 to 12 weeks with physiotherapy',
    icd10: 'M17.11',
    snomed: '179344001',
  },
  cabg: {
    term: 'CABG / Bypass',
    simple: 'Creates alternate blood flow routes around blocked heart arteries.',
    analogy: 'Building a traffic diversion road around a blocked highway.',
    duration: '3 to 6 hours',
    stay: 'Usually 5 to 8 nights',
    recovery: '6 to 12 weeks',
    icd10: 'I25.10',
    snomed: '232717009',
  },
  icu: {
    term: 'ICU',
    simple: 'Intensive Care Unit for close monitoring after serious procedures.',
    analogy: 'A high-monitoring zone with continuous care.',
    duration: 'Varies by condition',
    stay: 'Often 1 to 3 nights if needed',
    recovery: 'Depends on overall treatment pathway',
    icd10: 'Z99.11',
    snomed: '448951000124107',
  },
};

export function getTermDefinition(raw: string): TermDefinition | null {
  const key = raw.toLowerCase();
  if (TERM_MAP[key]) return TERM_MAP[key];
  if (key.includes('knee') && key.includes('replacement')) return TERM_MAP['knee replacement'];
  return null;
}

interface TermExplainerProps {
  term: TermDefinition;
}

export function TermExplainer({ term }: TermExplainerProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        className="underline decoration-dashed underline-offset-2 text-(--c-teal-700)"
        onClick={() => setOpen(true)}
        aria-label={`Explain medical term ${term.term}`}
      >
        {term.term}
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{term.term}</DialogTitle>
          </DialogHeader>

          <p className="text-sm text-muted-foreground">
            Plain-language explanation to help you prepare questions for your doctor.
          </p>

          <div className="space-y-3 text-sm">
            <Section title="What is it?" text={term.simple} />
            <Section title="In simple terms" text={term.analogy} />
            <Section title="How long?" text={term.duration} />
            <Section title="Hospital stay" text={term.stay} />
            <Section title="Recovery time" text={term.recovery} />
            <Section title="Medical codes" text={`ICD-10: ${term.icd10} · SNOMED CT: ${term.snomed}`} />
          </div>

          <p className="text-xs text-muted-foreground">
            This is educational only. Your doctor will advise whether this procedure is right for you.
          </p>

          <div className="flex justify-end">
            <Button size="sm" onClick={() => setOpen(false)}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function Section({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-md border border-border px-3 py-2">
      <p className="font-medium">{title}</p>
      <p className="text-muted-foreground">{text}</p>
    </div>
  );
}
