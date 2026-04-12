'use client';

import { useEffect, useState } from 'react';
import { Bell, Menu, Moon, User } from 'lucide-react';
import { useTheme } from 'next-themes';
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
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDarkMode = mounted && resolvedTheme === 'dark';

  return (
    <header className="shrink-0 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="flex h-16 items-center justify-between gap-3 px-4">
        <div className="flex min-w-0 items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
            aria-label="Open navigation menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex min-w-0 items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary shadow-sm">
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
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold leading-tight text-foreground">HealthNav</h1>
              <p className="hidden text-xs text-muted-foreground sm:block">Compare. Estimate. Decide.</p>
            </div>
          </div>
        </div>

        <button
          onClick={onOpenProfile}
          className="hidden max-w-[42vw] rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground md:inline-flex"
        >
          {location}
        </button>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <Button variant="ghost" size="icon" className="h-9 w-9" aria-label="Notifications">
            <Bell className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9"
            onClick={() => mounted && setTheme(isDarkMode ? 'light' : 'dark')}
            aria-label="Toggle dark mode"
          >
            <Moon className="h-4 w-4" />
          </Button>
          {state.patientProfile ? (
            <button
              onClick={onOpenProfile}
              className="flex items-center gap-2 transition-opacity hover:opacity-80"
            >
              <ProfileBadge profile={state.patientProfile} />
            </button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenProfile}
              className="text-muted-foreground hover:text-foreground"
            >
              <User className="mr-2 h-4 w-4" />
              <span className="hidden sm:inline">Add Location &amp; Budget</span>
              <span className="sm:hidden">Profile</span>
            </Button>
          )}
        </div>
      </div>

      <div className="border-t border-border px-4 py-2 md:hidden">
        <button
          onClick={onOpenProfile}
          className="flex w-full items-center justify-center rounded-full bg-muted px-3 py-2 text-xs text-muted-foreground"
        >
          {location}
        </button>
      </div>
    </header>
  );
}
