import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useFocusTrap } from './useFocusTrap';

function createContainer(): HTMLDivElement {
  const container = document.createElement('div');
  const btn1 = document.createElement('button');
  btn1.textContent = 'First';
  const btn2 = document.createElement('button');
  btn2.textContent = 'Second';
  const btn3 = document.createElement('button');
  btn3.textContent = 'Third';
  container.appendChild(btn1);
  container.appendChild(btn2);
  container.appendChild(btn3);
  document.body.appendChild(container);
  return container;
}

function fireKeyDown(target: HTMLElement, key: string, shiftKey = false) {
  const event = new KeyboardEvent('keydown', {
    key,
    shiftKey,
    bubbles: true,
    cancelable: true,
  });
  target.dispatchEvent(event);
  return event;
}

describe('useFocusTrap', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    container = createContainer();
  });

  afterEach(() => {
    container.remove();
  });

  it('moves focus to first focusable element on mount', () => {
    const ref = { current: container };
    renderHook(() => useFocusTrap(ref));

    const buttons = container.querySelectorAll('button');
    expect(document.activeElement).toBe(buttons[0]);
  });

  it('calls onEscape when Escape key is pressed', () => {
    const onEscape = vi.fn();
    const ref = { current: container };
    renderHook(() => useFocusTrap(ref, { onEscape }));

    fireKeyDown(container, 'Escape');
    expect(onEscape).toHaveBeenCalledTimes(1);
  });

  it('does not trap focus when enabled=false', () => {
    // Focus something outside the container first
    const outside = document.createElement('button');
    outside.textContent = 'Outside';
    document.body.appendChild(outside);
    outside.focus();

    const ref = { current: container };
    renderHook(() => useFocusTrap(ref, { enabled: false }));

    // Focus should remain on the outside element, not moved into the container
    expect(document.activeElement).toBe(outside);
    outside.remove();
  });

  it('wraps Tab from last focusable to first', () => {
    const ref = { current: container };
    renderHook(() => useFocusTrap(ref));

    const buttons = container.querySelectorAll('button');
    // Focus the last button
    buttons[2].focus();
    expect(document.activeElement).toBe(buttons[2]);

    // Press Tab on last element — should wrap to first
    fireKeyDown(container, 'Tab');
    expect(document.activeElement).toBe(buttons[0]);
  });

  it('wraps Shift+Tab from first focusable to last', () => {
    const ref = { current: container };
    renderHook(() => useFocusTrap(ref));

    const buttons = container.querySelectorAll('button');
    // Focus should already be on first
    expect(document.activeElement).toBe(buttons[0]);

    // Press Shift+Tab on first element — should wrap to last
    fireKeyDown(container, 'Tab', true);
    expect(document.activeElement).toBe(buttons[2]);
  });

  it('does not call onEscape for other keys', () => {
    const onEscape = vi.fn();
    const ref = { current: container };
    renderHook(() => useFocusTrap(ref, { onEscape }));

    fireKeyDown(container, 'Enter');
    fireKeyDown(container, 'a');
    fireKeyDown(container, 'ArrowDown');
    expect(onEscape).not.toHaveBeenCalled();
  });

  it('restores focus to previously focused element on unmount', () => {
    const outside = document.createElement('button');
    outside.textContent = 'Outside';
    document.body.appendChild(outside);
    outside.focus();
    expect(document.activeElement).toBe(outside);

    const ref = { current: container };
    const { unmount } = renderHook(() => useFocusTrap(ref));

    // Focus should have moved into the container
    const buttons = container.querySelectorAll('button');
    expect(document.activeElement).toBe(buttons[0]);

    // On unmount, focus should be restored
    unmount();
    expect(document.activeElement).toBe(outside);

    outside.remove();
  });
});
