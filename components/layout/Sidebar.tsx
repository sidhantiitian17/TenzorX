'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { useAppState, useAppDispatch } from '@/lib/context';
import { Button } from '@/components/ui/button';
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
  const [darkMode, setDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  const menuItems = [
    { icon: History, label: 'History', badge: state.conversation.length > 0 ? state.conversation.length : undefined },
    { icon: Bookmark, label: 'Saved Results', badge: undefined },
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
            onToggleLenderMode={onToggleLenderMode}
            onOpenProfile={onOpenProfile}
            onOpenSettings={onOpenSettings}
            onLoadQuery={onLoadQuery}
          />
        </motion.aside>
      </>
    );
  }

  // Desktop sidebar
  return (
    <aside
      className={cn(
        'hidden lg:flex flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      <div className="flex items-center justify-end p-2 border-b border-sidebar-border">
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
        onToggleLenderMode={onToggleLenderMode}
        onOpenProfile={onOpenProfile}
        onOpenSettings={onOpenSettings}
        onLoadQuery={onLoadQuery}
      />
    </aside>
  );
}

interface SidebarContentProps {
  menuItems: { icon: React.ElementType; label: string; badge?: number }[];
  collapsed: boolean;
  darkMode: boolean;
  toggleDarkMode: () => void;
  conversation: { id: string; content: string; timestamp: Date; role: string }[];
  onToggleLenderMode?: () => void;
  onOpenProfile?: () => void;
  onOpenSettings?: () => void;
  onLoadQuery?: (query: string) => void;
}

function SidebarContent({
  menuItems,
  collapsed,
  darkMode,
  toggleDarkMode,
  conversation,
  onToggleLenderMode,
  onOpenProfile,
  onOpenSettings,
  onLoadQuery,
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
              'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent transition-colors',
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

      {/* Dark mode toggle */}
      <div className="mt-auto px-2 pt-4 border-t border-sidebar-border">
        <button
          onClick={toggleDarkMode}
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent transition-colors',
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
