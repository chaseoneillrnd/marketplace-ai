import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AnnouncerProvider } from '../context/AnnouncerContext';
import { useAnnounce } from './useAnnounce';

function wrapper({ children }: { children: ReactNode }) {
  return <AnnouncerProvider>{children}</AnnouncerProvider>;
}

describe('useAnnounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('throws when used outside AnnouncerProvider', () => {
    expect(() => {
      renderHook(() => useAnnounce());
    }).toThrow('useAnnounce must be used within AnnouncerProvider');
  });

  it('returns an announce function', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });
    expect(typeof result.current.announce).toBe('function');
  });

  it('polite announcement sets role=status region text', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });

    act(() => {
      result.current.announce('Item saved', 'polite');
    });

    const statusRegion = document.querySelector('[role="status"]');
    expect(statusRegion).not.toBeNull();
    expect(statusRegion!.textContent).toBe('Item saved');
  });

  it('assertive announcement sets role=alert region text', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });

    act(() => {
      result.current.announce('Critical error', 'assertive');
    });

    const alertRegion = document.querySelector('[role="alert"]');
    expect(alertRegion).not.toBeNull();
    expect(alertRegion!.textContent).toBe('Critical error');
  });

  it('defaults to polite level when no level specified', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });

    act(() => {
      result.current.announce('Default level message');
    });

    const statusRegion = document.querySelector('[role="status"]');
    expect(statusRegion!.textContent).toBe('Default level message');

    const alertRegion = document.querySelector('[role="alert"]');
    expect(alertRegion!.textContent).toBe('');
  });

  it('does not announce empty or whitespace-only strings', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });

    act(() => {
      result.current.announce('', 'polite');
    });

    const statusRegion = document.querySelector('[role="status"]');
    expect(statusRegion!.textContent).toBe('');

    act(() => {
      result.current.announce('   ', 'assertive');
    });

    const alertRegion = document.querySelector('[role="alert"]');
    expect(alertRegion!.textContent).toBe('');
  });

  it('clears message after 7 seconds', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });

    act(() => {
      result.current.announce('Temporary message', 'polite');
    });

    const statusRegion = document.querySelector('[role="status"]');
    expect(statusRegion!.textContent).toBe('Temporary message');

    act(() => {
      vi.advanceTimersByTime(7000);
    });

    expect(statusRegion!.textContent).toBe('');
  });

  it('clears assertive message after 7 seconds', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });

    act(() => {
      result.current.announce('Alert message', 'assertive');
    });

    const alertRegion = document.querySelector('[role="alert"]');
    expect(alertRegion!.textContent).toBe('Alert message');

    act(() => {
      vi.advanceTimersByTime(7000);
    });

    expect(alertRegion!.textContent).toBe('');
  });

  it('polite and assertive regions are independent', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });

    act(() => {
      result.current.announce('Polite msg', 'polite');
      result.current.announce('Assertive msg', 'assertive');
    });

    const statusRegion = document.querySelector('[role="status"]');
    const alertRegion = document.querySelector('[role="alert"]');
    expect(statusRegion!.textContent).toBe('Polite msg');
    expect(alertRegion!.textContent).toBe('Assertive msg');
  });

  it('aria-live regions use visually-hidden styles, not display:none', () => {
    renderHook(() => useAnnounce(), { wrapper });

    const statusRegion = document.querySelector('[role="status"]') as HTMLElement;
    const alertRegion = document.querySelector('[role="alert"]') as HTMLElement;

    expect(statusRegion.style.position).toBe('absolute');
    expect(statusRegion.style.width).toBe('1px');
    expect(statusRegion.style.height).toBe('1px');
    expect(statusRegion.style.overflow).toBe('hidden');
    expect(statusRegion.style.display).not.toBe('none');

    expect(alertRegion.style.position).toBe('absolute');
    expect(alertRegion.style.display).not.toBe('none');
  });
});
