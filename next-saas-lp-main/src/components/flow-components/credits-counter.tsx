'use client';

import { CoinsIcon } from 'lucide-react';

// Credits counter disabled - requires auth setup
export const CreditCounter = () => {
  return (
    <div className="flex shrink-0 items-center gap-2 px-2 text-muted-foreground">
      <CoinsIcon size={16} />
      <span className="text-nowrap text-sm">Credits: ∞</span>
    </div>
  );
};
