import { useT } from '../../context/ThemeContext';

interface RevisionBadgeProps {
  revisionNumber: number;
}

export function RevisionBadge({ revisionNumber }: RevisionBadgeProps) {
  const C = useT();

  if (revisionNumber <= 1) return null;

  const isEscalated = revisionNumber >= 3;

  return (
    <span
      data-testid="revision-badge"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '10px',
        fontWeight: 600,
        padding: '2px 8px',
        borderRadius: '99px',
        background: isEscalated ? C.amberDim : C.accentDim,
        color: isEscalated ? C.amber : C.accent,
        lineHeight: '16px',
      }}
    >
      Round {revisionNumber}
    </span>
  );
}
