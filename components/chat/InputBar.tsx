'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, MapPin, User, Wallet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface InputBarProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  onOpenProfile?: () => void;
}

const MAX_CHARS = 500;
const SHOW_COUNTER_AT = 350;

export function InputBar({
  onSend,
  isLoading,
  onOpenProfile,
}: InputBarProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [value]);

  const handleSubmit = () => {
    if (value.trim() && !isLoading) {
      onSend(value.trim());
      setValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className="border-t border-border/80 bg-background/95 px-4 pb-4 pt-3 backdrop-blur supports-backdrop-filter:bg-background/80"
      aria-busy={isLoading}
    >
      <div className="mx-auto max-w-3xl">
        {/* Main input area */}
        <div className="rounded-2xl border border-border/70 bg-card/95 p-2 shadow-md">
          <div className="relative flex items-end gap-2">
            {/* Microphone button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-10 w-10 shrink-0 rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground"
              disabled={isLoading}
              aria-label="Voice input"
            >
              <Mic className="h-5 w-5" />
            </Button>

            {/* Text input */}
            <div className="relative flex-1">
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => setValue(e.target.value.slice(0, MAX_CHARS))}
                onKeyDown={handleKeyDown}
                placeholder="Describe condition, procedure, city, and budget..."
                disabled={isLoading}
                rows={1}
                maxLength={MAX_CHARS}
                className={cn(
                  'w-full resize-none bg-transparent text-sm leading-relaxed',
                  'placeholder:text-muted-foreground focus:outline-none',
                  'disabled:cursor-not-allowed disabled:opacity-50',
                  'py-2.5 pr-2'
                )}
              />
            </div>

            {/* Send button */}
            <Button
              onClick={handleSubmit}
              disabled={!value.trim() || isLoading}
              size="icon"
              className="h-10 w-10 shrink-0 rounded-xl bg-primary text-primary-foreground shadow-sm shadow-primary/35 hover:bg-primary/90"
            >
              {isLoading ? (
                <motion.div
                  className="h-5 w-5 rounded-full border-2 border-primary-foreground border-t-transparent"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>

          <div className="mt-1 flex items-center justify-between px-2 pb-1">
            <p className="text-[11px] text-muted-foreground">Enter to send, Shift+Enter for new line</p>

            {/* Character counter */}
            <AnimatePresence>
              {value.length > SHOW_COUNTER_AT && (
                <motion.span
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className={cn(
                    'mr-1 shrink-0 text-xs tabular-nums',
                    value.length >= MAX_CHARS ? 'text-destructive' : 'text-muted-foreground'
                  )}
                >
                  {value.length}/{MAX_CHARS}
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Filter chips - all open the profile modal */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <FilterChip
            icon={MapPin}
            label="Add Location"
            onClick={onOpenProfile}
          />
          <FilterChip
            icon={User}
            label="Patient Details"
            onClick={onOpenProfile}
          />
          <FilterChip
            icon={Wallet}
            label="Set Budget"
            onClick={onOpenProfile}
          />
        </div>
      </div>
    </div>
  );
}

interface FilterChipProps {
  icon: React.ElementType;
  label: string;
  onClick?: () => void;
  active?: boolean;
}

function FilterChip({ icon: Icon, label, onClick, active }: FilterChipProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
        active
          ? 'border-primary bg-primary text-primary-foreground'
          : 'border-border/60 bg-card text-muted-foreground hover:border-border hover:bg-secondary/70 hover:text-foreground'
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </button>
  );
}
