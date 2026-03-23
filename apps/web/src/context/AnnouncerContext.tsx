import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';

type Level = 'polite' | 'assertive';

interface AnnouncerContextValue {
  announce: (message: string, level?: Level) => void;
}

const AnnouncerContext = createContext<AnnouncerContextValue | null>(null);

export function useAnnouncerContext(): AnnouncerContextValue {
  const ctx = useContext(AnnouncerContext);
  if (!ctx) throw new Error('useAnnounce must be used within AnnouncerProvider');
  return ctx;
}

const srOnly: React.CSSProperties = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0,0,0,0)',
  whiteSpace: 'nowrap',
  border: 0,
};

export function AnnouncerProvider({ children }: { children: ReactNode }) {
  const [politeMsg, setPoliteMsg] = useState('');
  const [assertiveMsg, setAssertiveMsg] = useState('');
  const politeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const assertiveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const announce = useCallback((message: string, level: Level = 'polite') => {
    if (!message.trim()) return;

    if (level === 'polite') {
      if (politeTimerRef.current) clearTimeout(politeTimerRef.current);
      setPoliteMsg(message);
      politeTimerRef.current = setTimeout(() => {
        setPoliteMsg('');
        politeTimerRef.current = null;
      }, 7000);
    } else {
      if (assertiveTimerRef.current) clearTimeout(assertiveTimerRef.current);
      setAssertiveMsg(message);
      assertiveTimerRef.current = setTimeout(() => {
        setAssertiveMsg('');
        assertiveTimerRef.current = null;
      }, 7000);
    }
  }, []);

  return (
    <AnnouncerContext.Provider value={{ announce }}>
      {children}
      <div role="status" aria-live="polite" style={srOnly}>
        {politeMsg}
      </div>
      <div role="alert" aria-live="assertive" style={srOnly}>
        {assertiveMsg}
      </div>
    </AnnouncerContext.Provider>
  );
}
