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
    <div className="border-t border-border bg-card p-4" aria-busy={isLoading}>
      <div className="max-w-3xl mx-auto">
        {/* Main input area */}
        <div className="relative flex items-end gap-2 bg-secondary rounded-2xl p-2">
          {/* Microphone button */}
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 shrink-0 text-muted-foreground hover:text-foreground"
            disabled={isLoading}
            aria-label="Voice input"
          >
            <Mic className="h-5 w-5" />
          </Button>

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => setValue(e.target.value.slice(0, MAX_CHARS))}
              onKeyDown={handleKeyDown}
              placeholder="Describe your condition or procedure..."
              disabled={isLoading}
              rows={1}
              maxLength={MAX_CHARS}
              className={cn(
                'w-full resize-none bg-transparent text-sm leading-relaxed',
                'placeholder:text-muted-foreground focus:outline-none',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'py-2.5 pr-2'
              )}
            />
          </div>

          {/* Character counter */}
          <AnimatePresence>
            {value.length > SHOW_COUNTER_AT && (
              <motion.span
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className={cn(
                  'text-xs tabular-nums shrink-0 mr-2',
                  value.length >= MAX_CHARS ? 'text-destructive' : 'text-muted-foreground'
                )}
              >
                {value.length}/{MAX_CHARS}
              </motion.span>
            )}
          </AnimatePresence>

          {/* Send button */}
          <Button
            onClick={handleSubmit}
            disabled={!value.trim() || isLoading}
            size="icon"
            className="h-10 w-10 shrink-0 rounded-xl"
          >
            {isLoading ? (
              <motion.div
                className="h-5 w-5 border-2 border-primary-foreground border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Filter chips - all open the profile modal */}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
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
        'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
        active
          ? 'bg-primary text-primary-foreground'
          : 'bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80'
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </button>
  );
}
