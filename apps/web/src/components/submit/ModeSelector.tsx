import { useT } from '../../context/ThemeContext';
import type { SubmitMode } from '../../views/submit/SubmitSkillPage';

interface ModeSelectorProps {
  mode: SubmitMode;
  onModeChange: (mode: SubmitMode) => void;
}

interface ModeOption {
  key: SubmitMode;
  icon: string;
  label: string;
  badge?: string;
}

const MODES: ModeOption[] = [
  { key: 'form', icon: '\u{1F4CB}', label: 'Guided Form' },
  { key: 'upload', icon: '\u{1F4E4}', label: 'Upload .md' },
  { key: 'mcp', icon: '\u{1F4BB}', label: 'MCP Sync', badge: 'Advanced' },
];

export function ModeSelector({ mode, onModeChange }: ModeSelectorProps) {
  const C = useT();

  return (
    <div
      role="tablist"
      aria-label="Submission mode"
      style={{
        display: 'flex',
        gap: '8px',
        borderBottom: `1px solid ${C.border}`,
        paddingBottom: '0',
      }}
    >
      {MODES.map((m) => {
        const active = mode === m.key;
        return (
          <button
            key={m.key}
            role="tab"
            aria-selected={active}
            aria-controls={`panel-${m.key}`}
            onClick={() => onModeChange(m.key)}
            data-testid={`mode-tab-${m.key}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 16px',
              fontSize: '13px',
              fontWeight: active ? 600 : 400,
              color: active ? C.accent : C.muted,
              background: 'none',
              border: 'none',
              borderBottom: active ? `2px solid ${C.accent}` : '2px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s',
              marginBottom: '-1px',
            }}
          >
            <span style={{ fontSize: '15px' }}>{m.icon}</span>
            {m.label}
            {m.badge && (
              <span
                style={{
                  fontSize: '10px',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: C.accentDim,
                  color: C.accent,
                  fontFamily: "'JetBrains Mono',monospace",
                  fontWeight: 600,
                }}
              >
                {m.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
