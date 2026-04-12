'use client';

import { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import type { Message } from '@/types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { InputBar } from './InputBar';
import { EmergencyBanner } from './EmergencyBanner';
import { suggestionChips } from '@/lib/mockData';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onOpenProfile?: () => void;
  showEmergency: boolean;
  onDismissEmergency: () => void;
}

export function ChatWindow({
  messages,
  isLoading,
  onSendMessage,
  onOpenProfile,
  showEmergency,
  onDismissEmergency,
}: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasMessages = messages.length > 0;

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {showEmergency && (
          <div className="mx-auto mt-4 w-full max-w-3xl px-4">
            <EmergencyBanner onDismiss={onDismissEmergency} />
          </div>
        )}
        {!hasMessages ? (
          <HeroSection onSelectSuggestion={onSendMessage} />
        ) : (
          <div className="p-4 space-y-4 max-w-3xl mx-auto">
            {messages.map((message, index) => (
              <MessageBubble
                key={message.id}
                message={message}
                isLatest={index === messages.length - 1 && message.role === 'assistant'}
              />
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <svg
                    className="h-4 w-4 text-primary"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                </div>
                <div className="bg-card border border-border shadow-sm rounded-2xl rounded-bl-md">
                  <TypingIndicator />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <InputBar
        onSend={onSendMessage}
        isLoading={isLoading}
        onOpenProfile={onOpenProfile}
      />
    </div>
  );
}

interface HeroSectionProps {
  onSelectSuggestion: (query: string) => void;
}

function HeroSection({ onSelectSuggestion }: HeroSectionProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-full p-8 text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-lg"
      >
        {/* Logo */}
        <div className="h-16 w-16 rounded-2xl bg-primary flex items-center justify-center mx-auto mb-6">
          <svg
            className="h-8 w-8 text-primary-foreground"
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

        {/* Headline */}
        <h2 className="text-2xl sm:text-3xl font-semibold text-foreground mb-3 text-balance">
          Find the right hospital. Know the real cost.
        </h2>

        {/* Subline */}
        <p className="text-muted-foreground mb-8 text-balance">
          Describe your condition in plain language — we&apos;ll handle the rest.
        </p>

        {/* Suggestion chips */}
        <div className="flex flex-wrap justify-center gap-2">
          {suggestionChips.map((suggestion) => (
            <motion.button
              key={suggestion}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelectSuggestion(suggestion)}
              className="px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-full text-sm text-secondary-foreground transition-colors"
            >
              {suggestion}
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
