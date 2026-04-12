'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface RankingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const weights = [
  {
    title: 'Clinical Capability (35%)',
    points: [
      'Specialization relevance to the procedure',
      'Procedure volume and depth of expertise',
    ],
  },
  {
    title: 'Reputation (30%)',
    points: [
      'Public ratings and review trends',
      'NLP sentiment from patient testimonials',
      'NABH accreditation status',
    ],
  },
  {
    title: 'Accessibility (20%)',
    points: ['Distance from your location', 'Estimated appointment availability'],
  },
  {
    title: 'Affordability (15%)',
    points: ['Tier fit for your budget', 'Cost benchmark relative to regional average'],
  },
];

export function RankingModal({ open, onOpenChange }: RankingModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>How Ranking Works</DialogTitle>
        </DialogHeader>

        <p className="text-sm text-muted-foreground">
          Hospitals are ranked by a weighted score designed to balance quality, access, and affordability.
        </p>

        <div className="space-y-3 text-sm">
          {weights.map((group) => (
            <div key={group.title} className="rounded-lg border border-border p-3">
              <p className="font-semibold">{group.title}</p>
              <ul className="mt-2 space-y-1 text-muted-foreground list-disc pl-4">
                {group.points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <p className="text-xs text-muted-foreground">
          We do not accept payments to influence rankings. Results are algorithm-driven.
        </p>
      </DialogContent>
    </Dialog>
  );
}
