'use client';

import { createContext, useContext, ReactNode } from 'react';

export type SubscriptionPlan = 'hobby' | 'pro' | 'enterprise';

export type SubscriptionContextType = {
  plan: SubscriptionPlan;
  isSubscribed: boolean;
};

const SubscriptionContext = createContext<SubscriptionContextType>({
  plan: 'pro',
  isSubscribed: true,
});

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within SubscriptionProvider');
  }
  return context;
};

export const SubscriptionProvider = ({ children }: { children: ReactNode }) => {
  // Mock subscription - all features enabled
  return (
    <SubscriptionContext.Provider
      value={{
        plan: 'pro',
        isSubscribed: true,
      }}
    >
      {children}
    </SubscriptionContext.Provider>
  );
};
