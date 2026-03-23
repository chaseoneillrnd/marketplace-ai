---
name: component-library-builder
description: Use when building shared React components in libs/ui/ or apps/web/src/components/
---

# Component Library Builder

## Component Pattern

```tsx
// apps/web/src/components/MyComponent.tsx
interface MyComponentProps {
  title: string;
  variant?: 'default' | 'featured';
  onClick?: () => void;
}

export function MyComponent({ title, variant = 'default', onClick }: MyComponentProps) {
  return (
    <div className={`my-component my-component--${variant}`} onClick={onClick}>
      <h3>{title}</h3>
    </div>
  );
}
```

## Existing Components

| Component | File | Purpose |
|-----------|------|---------|
| SkillCard | components/SkillCard.tsx | Grid card for skill listings |
| Nav | components/Nav.tsx | Top navigation bar |
| DivisionChip | components/DivisionChip.tsx | Division badge/pill |
| SkeletonCard | components/SkeletonCard.tsx | Loading placeholder |
| AuthModal | components/AuthModal.tsx | Login/signup modal |

## libs/ui (future)

Shared components will move to `libs/ui/src/` and export via `@skillhub/ui`. Currently components live in `apps/web/src/components/`.

## References

- Components: `apps/web/src/components/`
- UI lib: `libs/ui/`
- Design tokens: `design/tokens.json`
