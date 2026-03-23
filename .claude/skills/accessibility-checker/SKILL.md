---
name: accessibility-checker
description: Use when reviewing or implementing accessibility in the React frontend
---

# Accessibility Checker

## Key Areas

- ARIA roles on interactive elements
- Keyboard navigation (Tab, Enter, Escape)
- Color contrast (check design/tokens.json values)
- Focus management in modals (AuthModal)
- Screen reader text for icons/badges
- Form labels and error associations

## Modal Focus Trap

```tsx
useEffect(() => {
  if (isOpen) modalRef.current?.focus();
  const handleEsc = (e) => e.key === 'Escape' && onClose();
  document.addEventListener('keydown', handleEsc);
  return () => document.removeEventListener('keydown', handleEsc);
}, [isOpen]);
```

## References

- AuthModal: `apps/web/src/components/AuthModal.tsx`
- Design tokens: `design/tokens.json`
