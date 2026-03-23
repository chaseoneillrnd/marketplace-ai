import { DIVISION_COLORS, DIVISION_NAME_MAP } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';

interface Props {
  division: string;
  active?: boolean;
  onClick?: () => void;
  small?: boolean;
}

export function DivisionChip({ division, active = false, onClick, small = false }: Props) {
  const color = DIVISION_COLORS[division] ?? '#888';
  const displayName = DIVISION_NAME_MAP[division] ?? division;
  return (
    <span
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      style={{
        fontSize: small ? '9px' : '10px',
        padding: small ? '2px 6px' : '3px 9px',
        borderRadius: '99px',
        fontWeight: 600,
        fontFamily: "'JetBrains Mono',monospace",
        background: active ? `${color}25` : `${color}14`,
        color,
        border: `1px solid ${active ? color + '66' : color + '22'}`,
        whiteSpace: 'nowrap',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.12s',
        boxShadow: active ? `0 0 0 2px ${color}22` : 'none',
      }}
    >
      {displayName}
    </span>
  );
}

export function DivisionFilterBar({
  selected,
  onToggle,
  onClear,
  divisions,
}: {
  selected: string[];
  onToggle: (d: string) => void;
  onClear: () => void;
  divisions: readonly string[];
}) {
  const C = useT();
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        flexWrap: 'wrap',
        padding: '10px 14px',
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: '10px',
      }}
    >
      <span
        style={{
          fontSize: '10px',
          color: C.dim,
          fontWeight: 600,
          fontFamily: "'JetBrains Mono',monospace",
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
          flexShrink: 0,
          marginRight: '4px',
        }}
      >
        Division
      </span>
      {divisions.map((d) => (
        <DivisionChip key={d} division={d} active={selected.includes(d)} onClick={() => onToggle(d)} />
      ))}
      {selected.length > 0 && (
        <button
          onClick={onClear}
          style={{
            fontSize: '10px',
            color: C.dim,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            marginLeft: '4px',
            padding: '2px 6px',
            borderRadius: '4px',
          }}
        >
          Clear all
        </button>
      )}
    </div>
  );
}
