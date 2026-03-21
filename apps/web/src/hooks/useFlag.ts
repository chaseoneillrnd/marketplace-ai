import { useContext } from 'react';
import { FlagsContext, type FlagsContextValue } from '../context/FlagsContext';

export function useFlags(): FlagsContextValue {
  const ctx = useContext(FlagsContext);
  if (!ctx) {
    throw new Error('useFlags must be used within a FlagsProvider');
  }
  return ctx;
}

export function useFlag(key: string): boolean {
  const { flags } = useFlags();
  return flags[key] ?? false;
}
