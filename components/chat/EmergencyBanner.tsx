'use client';

import { AlertTriangle, PhoneCall } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmergencyBannerProps {
  onDismiss: () => void;
}

export function EmergencyBanner({ onDismiss }: EmergencyBannerProps) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-900 shadow-sm">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
        <div className="space-y-2">
          <p className="text-sm font-semibold">Medical emergency?</p>
          <p className="text-sm leading-relaxed">
            If you or someone you know has severe chest pain, stroke symptoms, heavy bleeding,
            breathing distress, or loss of consciousness, call 112 immediately.
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <Button asChild className="h-9">
              <a href="tel:112">
                <PhoneCall className="mr-2 h-4 w-4" />
                Call 112
              </a>
            </Button>
            <Button variant="outline" className="h-9" onClick={onDismiss}>
              I am just researching
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
