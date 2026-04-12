'use client';

import { motion } from 'framer-motion';

export function TypingIndicator() {
  return (
    <div role="status" aria-live="polite" className="p-3">
      <div className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 bg-primary rounded-full"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              delay: i * 0.2,
            }}
          />
        ))}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">Analyzing your query...</p>
    </div>
  );
}
