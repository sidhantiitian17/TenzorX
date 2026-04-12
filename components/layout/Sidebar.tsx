'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from 'next-themes';
import {
  History,
  Bookmark,
  User,
  Settings,
  X,
  ChevronLeft,
  ChevronRight,
  Moon,
  Sun,
  MessageSquare,
  Landmark,
  Calendar,
  PanelLeft,
} from 'lucide-react';
import { useAppState, useAppDispatch } from '@/lib/context';
import { Button } from '@/components/ui/button';
import type { AppointmentRequest, AppointmentStatus } from '@/types';
import { cn } from '@/lib/utils';
import { formatTimestamp } from '@/lib/formatters';

interface SidebarProps {
  className?: string;
  onToggleLenderMode?: () => void;
  onOpenProfile?: () => void;
  onOpenSettings?: () => void;
  onLoadQuery?: (query: string) => void;
}

export function Sidebar({ className, onToggleLenderMode, onOpenProfile, onOpenSettings, onLoadQuery }: SidebarProps) {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const [collapsed, setCollapsed] = useState(false);
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const darkMode = mounted && resolvedTheme === 'dark';

  const toggleDarkMode = () => {
    if (!mounted) return;
    setTheme(darkMode ? 'light' : 'dark');
  };

  const menuItems = [
    { icon: History, label: 'History', badge: state.conversation.length > 0 ? state.conversation.length : undefined },
    { icon: Bookmark, label: 'Saved Results', badge: undefined },
    { icon: Calendar, label: 'My Appointment Requests', badge: state.appointmentRequests.length > 0 ? state.appointmentRequests.length : undefined },
    { icon: User, label: 'Patient Profile', badge: state.patientProfile ? 1 : undefined },
    { icon: Landmark, label: state.lenderMode ? 'Lender Mode: ON' : 'Lender / Insurer Mode', badge: undefined },
    { icon: Settings, label: 'Settings', badge: undefined },
  ];

  // Mobile overlay
  if (state.sidebarOpen) {
    return (
      <>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
        />
        <motion.aside
          initial={{ x: -280 }}
          animate={{ x: 0 }}
          exit={{ x: -280 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="fixed left-0 top-0 bottom-0 w-72 bg-sidebar border-r border-sidebar-border z-50 lg:hidden"
        >
          <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
            <h2 className="font-semibold">Menu</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          <SidebarContent
            menuItems={menuItems}
            collapsed={false}
            darkMode={darkMode}
            toggleDarkMode={toggleDarkMode}
            conversation={state.conversation}
            appointmentRequests={state.appointmentRequests}
            onToggleLenderMode={onToggleLenderMode}
            onOpenProfile={onOpenProfile}
            onOpenSettings={onOpenSettings}
            onLoadQuery={onLoadQuery}
            onUpdateAppointmentStatus={(id, status) => dispatch({ type: 'SET_APPOINTMENT_REQUEST_STATUS', payload: { id, status } })}
            onRemoveAppointmentRequest={(id) => dispatch({ type: 'REMOVE_APPOINTMENT_REQUEST', payload: id })}
          />
        </motion.aside>
      </>
    );
  }

  // Desktop sidebar rail for lg-xl and full sidebar for xl+
  return (
    <>
      <aside
        className={cn(
          'hidden lg:flex xl:hidden flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300 w-16',
          className
        )}
      >
        <div className="flex items-center justify-center border-b border-sidebar-border p-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
            aria-label="Open navigation drawer"
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
        </div>
        <SidebarContent
          menuItems={menuItems}
          collapsed
          darkMode={darkMode}
          toggleDarkMode={toggleDarkMode}
          conversation={state.conversation}
          appointmentRequests={state.appointmentRequests}
          onToggleLenderMode={onToggleLenderMode}
          onOpenProfile={onOpenProfile}
          onOpenSettings={onOpenSettings}
          onLoadQuery={onLoadQuery}
          onUpdateAppointmentStatus={(id, status) => dispatch({ type: 'SET_APPOINTMENT_REQUEST_STATUS', payload: { id, status } })}
          onRemoveAppointmentRequest={(id) => dispatch({ type: 'REMOVE_APPOINTMENT_REQUEST', payload: id })}
        />
      </aside>

      <aside
        className={cn(
          'hidden xl:flex flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300',
          collapsed ? 'w-16' : 'w-64',
          className
        )}
      >
        <div className="flex items-center justify-end border-b border-sidebar-border p-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="h-8 w-8"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>
        <SidebarContent
          menuItems={menuItems}
          collapsed={collapsed}
          darkMode={darkMode}
          toggleDarkMode={toggleDarkMode}
          conversation={state.conversation}
          appointmentRequests={state.appointmentRequests}
          onToggleLenderMode={onToggleLenderMode}
          onOpenProfile={onOpenProfile}
          onOpenSettings={onOpenSettings}
          onLoadQuery={onLoadQuery}
          onUpdateAppointmentStatus={(id, status) => dispatch({ type: 'SET_APPOINTMENT_REQUEST_STATUS', payload: { id, status } })}
          onRemoveAppointmentRequest={(id) => dispatch({ type: 'REMOVE_APPOINTMENT_REQUEST', payload: id })}
        />
      </aside>
    </>
  );
}

interface SidebarContentProps {
  menuItems: { icon: React.ElementType; label: string; badge?: number }[];
  collapsed: boolean;
  darkMode: boolean;
  toggleDarkMode: () => void;
  conversation: { id: string; content: string; timestamp: Date; role: string }[];
  appointmentRequests: AppointmentRequest[];
  onToggleLenderMode?: () => void;
  onOpenProfile?: () => void;
  onOpenSettings?: () => void;
  onLoadQuery?: (query: string) => void;
  onUpdateAppointmentStatus?: (id: string, status: AppointmentStatus) => void;
  onRemoveAppointmentRequest?: (id: string) => void;
}

function SidebarContent({
  menuItems,
  collapsed,
  darkMode,
  toggleDarkMode,
  conversation,
  appointmentRequests,
  onToggleLenderMode,
  onOpenProfile,
  onOpenSettings,
  onLoadQuery,
  onUpdateAppointmentStatus,
  onRemoveAppointmentRequest,
}: SidebarContentProps) {
  const handleMenuClick = (label: string) => {
    if (label.includes('Lender')) {
      onToggleLenderMode?.();
    } else if (label === 'Patient Profile') {
      onOpenProfile?.();
    } else if (label === 'Settings') {
      onOpenSettings?.();
    } else if (label === 'History') {
      // History button - could show a history panel or modal
      console.log('History clicked');
    } else if (label === 'Saved Results') {
      // Saved results button
      console.log('Saved Results clicked');
    }
  };
  return (
    <div className="flex flex-col flex-1 py-4 overflow-hidden">
      <nav className="space-y-1 px-2">
        {menuItems.map((item) => (
          <button
            key={item.label}
            onClick={() => handleMenuClick(item.label)}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent transition-colors min-h-11',
              collapsed && 'justify-center'
            )}
            aria-label={item.label}
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!collapsed && (
              <>
                <span className="flex-1 text-left text-sm">{item.label}</span>
                {item.badge && (
                  <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </button>
        ))}
      </nav>

      {/* Recent queries */}
      {!collapsed && conversation.length > 0 && (
        <div className="mt-6 px-3">
          <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
            Recent Queries
          </h3>
          <div className="space-y-1">
            {conversation
              .filter((m) => m.role === 'user')
              .slice(-5)
              .reverse()
              .map((message) => (
                <button
                  key={message.id}
                  onClick={() => onLoadQuery?.(message.content)}
                  className="w-full flex items-start gap-2 px-2 py-1.5 rounded text-left text-sm hover:bg-sidebar-accent transition-colors"
                  title={message.content}
                >
                  <MessageSquare className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sidebar-foreground">
                      {message.content.slice(0, 30)}...
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatTimestamp(new Date(message.timestamp))}
                    </p>
                  </div>
                </button>
              ))}
          </div>
        </div>
      )}

      {!collapsed && (
        <div className="mt-6 px-3">
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            My Appointment Requests
          </h3>
          {appointmentRequests.length === 0 ? (
            <p className="rounded-md border border-dashed border-sidebar-border px-2 py-2 text-xs text-muted-foreground">
              No appointment requests yet.
            </p>
          ) : (
            <div className="max-h-44 space-y-2 overflow-y-auto pr-1">
              {[...appointmentRequests]
                .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
                .slice(0, 6)
                .map((request) => (
                  <div key={request.id} className="rounded-md border border-sidebar-border bg-sidebar-accent/40 px-2 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-xs font-medium text-sidebar-foreground">{request.doctorName}</p>
                      <span className={cn(
                        'rounded-full px-1.5 py-0.5 text-[10px] font-medium',
                        request.status === 'confirmed'
                          ? 'bg-emerald-100 text-emerald-700'
                          : request.status === 'cancelled'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-amber-100 text-amber-700'
                      )}>
                        {request.status}
                      </span>
                    </div>
                    <p className="mt-0.5 truncate text-[11px] text-muted-foreground">{request.hospitalName}</p>
                    <p className="truncate text-[11px] text-muted-foreground">{request.slot}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {request.status !== 'confirmed' && request.status !== 'cancelled' && (
                        <button
                          onClick={() => onUpdateAppointmentStatus?.(request.id, 'confirmed')}
                          className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700"
                        >
                          Mark Confirmed
                        </button>
                      )}
                      {request.status !== 'cancelled' && (
                        <button
                          onClick={() => onUpdateAppointmentStatus?.(request.id, 'cancelled')}
                          className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-medium text-red-700"
                        >
                          Cancel
                        </button>
                      )}
                      <button
                        onClick={() => onRemoveAppointmentRequest?.(request.id)}
                        className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Dark mode toggle */}
      <div className="mt-auto px-2 pt-4 border-t border-sidebar-border">
        <button
          onClick={toggleDarkMode}
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent transition-colors min-h-11',
            collapsed && 'justify-center'
          )}
        >
          {darkMode ? (
            <Sun className="h-5 w-5 shrink-0" />
          ) : (
            <Moon className="h-5 w-5 shrink-0" />
          )}
          {!collapsed && (
            <span className="text-sm">{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
          )}
        </button>
      </div>
    </div>
  );
}
