'use client';

import { motion } from 'framer-motion';
import { ThumbsUp, ThumbsDown, RefreshCw, Stethoscope, Copy, UserRound } from 'lucide-react';
import type { Message } from '@/types';
import { formatTimestamp } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { getTermDefinition, TermExplainer } from '@/components/education/TermExplainer';

interface MessageBubbleProps {
  message: Message;
  isLatest?: boolean;
}

export function MessageBubble({ message, isLatest }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
    } catch {
      // Ignore clipboard failures in unsupported contexts.
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn('flex w-full items-end gap-3', isUser ? 'justify-end' : 'justify-start')}
    >
      {/* AI Avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <Stethoscope className="h-4 w-4 text-primary" />
        </div>
      )}

      <div className={cn('flex max-w-[88%] flex-col sm:max-w-[82%]', isUser ? 'items-end' : 'items-start')}>
        {isUser && (
          <p className="mb-1 px-1 text-[11px] font-medium tracking-wide text-muted-foreground">
            You
          </p>
        )}

        {/* Message bubble */}
        <div
          className={cn(
            'rounded-2xl px-4 py-3 shadow-sm',
            isUser
              ? 'rounded-tr-md border border-primary/25 bg-linear-to-br from-primary to-primary/85 text-primary-foreground'
              : 'rounded-bl-md border border-border bg-card'
          )}
        >
          <div
            className={cn(
              'text-sm leading-relaxed whitespace-pre-wrap',
              isUser ? 'text-primary-foreground' : 'text-card-foreground'
            )}
          >
            <MessageContent content={message.content} interactiveTerms={!isUser} />
          </div>
        </div>

        {/* Timestamp */}
        <p className="mt-1 px-1 text-xs text-muted-foreground">
          {formatTimestamp(new Date(message.timestamp))}
        </p>

        {/* Feedback buttons for AI messages */}
        {!isUser && isLatest && (
          <div className="mt-2 flex items-center gap-1">
            <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-foreground">
              <ThumbsUp className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-foreground">
              <ThumbsDown className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-foreground">
              <RefreshCw className="h-3.5 w-3.5 mr-1" />
              <span className="text-xs">Refine</span>
            </Button>
            <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-foreground" onClick={onCopy}>
              <Copy className="h-3.5 w-3.5 mr-1" />
              <span className="text-xs">Copy</span>
            </Button>
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
          <UserRound className="h-4 w-4" />
        </div>
      )}
    </motion.div>
  );
}

function MessageContent({
  content,
  interactiveTerms = true,
}: {
  content: string;
  interactiveTerms?: boolean;
}) {
  const lines = content.split('\n');

  return (
    <>
      {lines.map((line, i) => {
        // Handle bold text
        const parts = line.split(/\*\*(.*?)\*\*/g);
        const formattedLine = parts.map((part, j) =>
          j % 2 === 1 ? <strong key={j}>{renderWithTerms(part, interactiveTerms)}</strong> : renderWithTerms(part, interactiveTerms)
        );

        // Handle bullet points
        if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
          return (
            <div key={i} className="flex items-start gap-2 ml-2">
              <span className="text-primary mt-1">•</span>
              <span>{formattedLine}</span>
            </div>
          );
        }

        return (
          <span key={i}>
            {formattedLine}
            {i < lines.length - 1 && <br />}
          </span>
        );
      })}
    </>
  );
}

function renderWithTerms(text: string, interactiveTerms: boolean) {
  if (!interactiveTerms) {
    return text;
  }

  const terms = ['angioplasty', 'knee replacement', 'cabg', 'ICU'];
  const regex = new RegExp(`(${terms.join('|')})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) => {
    const definition = getTermDefinition(part);
    if (!definition) {
      return <span key={`${part}-${index}`}>{part}</span>;
    }
    return <TermExplainer key={`${part}-${index}`} term={definition} />;
  });
}
