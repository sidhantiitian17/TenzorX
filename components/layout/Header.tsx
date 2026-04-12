'use client';

import { Menu, User, Settings2 } from 'lucide-react';
import { useAppState, useAppDispatch } from '@/lib/context';
import { Button } from '@/components/ui/button';
import { ProfileBadge } from '@/components/profile/ProfileBadge';

interface HeaderProps {
  onOpenProfile?: () => void;
}

export function Header({ onOpenProfile }: HeaderProps) {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const location = state.patientProfile?.location || 'Nagpur, MH';

  return (
    <header className="h-16 border-b border-border bg-card flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <svg
              className="h-5 w-5 text-primary-foreground"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <div>
            <h1 className="font-semibold text-lg leading-tight">HealthNav</h1>
            <p className="text-xs text-muted-foreground hidden sm:block">Compare. Estimate. Decide.</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onOpenProfile}
          className="hidden md:inline-flex rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground"
        >
          {location}
        </button>
        {state.patientProfile ? (
          <button 
            onClick={onOpenProfile}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <ProfileBadge profile={state.patientProfile} />
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Settings2 className="h-4 w-4 text-muted-foreground" />
            </Button>
          </button>
        ) : (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onOpenProfile}
            className="text-muted-foreground hover:text-foreground"
          >
            <User className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Add Location &amp; Budget</span>
            <span className="sm:hidden">Profile</span>
          </Button>
        )}
      </div>
    </header>
  );
}
