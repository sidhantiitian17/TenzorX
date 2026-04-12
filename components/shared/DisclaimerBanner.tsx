'use client';

import { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function DisclaimerBanner() {
  const [isMinimized, setIsMinimized] = useState(false);

  return (
    <div className="sticky top-0 z-50 border-l-4 border-amber-600 bg-(--c-saffron-lt) text-amber-900">
      <AnimatePresence mode="wait">
        {isMinimized ? (
          <motion.button
            key="minimized"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            onClick={() => setIsMinimized(false)}
            className="w-full flex items-center justify-center gap-2 py-0.5 px-4 hover:bg-amber-100 transition-colors"
          >
            <AlertTriangle className="h-3.5 w-3.5" />
            <span className="text-xs font-medium">HealthNav disclaimer hidden. Click to expand.</span>
            <ChevronDown className="h-3.5 w-3.5" />
          </motion.button>
        ) : (
          <motion.div
            key="expanded"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center justify-between gap-4 py-2.5 px-4"
          >
            <div className="flex items-center gap-3 flex-1">
              <AlertTriangle className="h-5 w-5 shrink-0" />
              <p className="text-sm">
                HealthNav provides decision support only, not medical advice. Always consult a qualified doctor before making health decisions.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button className="text-xs font-medium underline underline-offset-2">Learn more</button>
              <button
                onClick={() => setIsMinimized(true)}
                className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-amber-100 transition-colors shrink-0"
                aria-label="Minimize disclaimer"
              >
                Hide
                <ChevronUp className="h-3.5 w-3.5" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
