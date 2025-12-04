'use client';

import { createContext, useContext, ReactNode } from 'react';
import type { PriceBracket } from '@/lib/providers';

export type TersaTextModel = {
  id: string;
  label: string;
  provider: string;
  priceIndicator: PriceBracket;
};

type GatewayContextType = {
  textModels: Record<string, TersaTextModel>;
};

const GatewayContext = createContext<GatewayContextType | undefined>(undefined);

export const useGateway = () => {
  const context = useContext(GatewayContext);
  if (!context) {
    throw new Error('useGateway must be used within GatewayProvider');
  }
  return context;
};

export const GatewayProviderClient = ({
  children,
  models,
}: {
  children: ReactNode;
  models: Record<string, TersaTextModel>;
}) => {
  return (
    <GatewayContext.Provider value={{ textModels: models }}>
      {children}
    </GatewayContext.Provider>
  );
};
