import { useState } from 'react';
import { useT } from '../../context/ThemeContext';

interface Props {
  onSubmit: (data: { frontMatter: Record<string, unknown>; content: string }) => void;
}

interface PlaceholderSkill {
  name: string;
  description: string;
}

const PLACEHOLDER_SKILLS: PlaceholderSkill[] = [
  { name: 'Code Review Assistant', description: 'Automated code review with best practices' },
  { name: 'API Documentation Generator', description: 'Generate OpenAPI specs from code' },
  { name: 'Test Suite Builder', description: 'Scaffold comprehensive test suites' },
];

export function MCPSyncMode({ onSubmit }: Props) {
  const C = useT();
  const [expanded, setExpanded] = useState(false);
  const [url, setUrl] = useState('');
  const [introspected, setIntrospected] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState<PlaceholderSkill | null>(null);
  const [confirming, setConfirming] = useState(false);

  const handleIntrospect = () => {
    setIntrospected(true);
    setSelectedSkill(null);
    setConfirming(false);
  };

  const handleSelect = (skill: PlaceholderSkill) => {
    setSelectedSkill(skill);
    setConfirming(true);
  };

  const handleConfirm = () => {
    if (!selectedSkill) return;
    onSubmit({
      frontMatter: {
        name: selectedSkill.name,
        description: selectedSkill.description,
        category: 'automation',
        tags: ['mcp', 'imported'],
      },
      content: `# ${selectedSkill.name}\n\n${selectedSkill.description}\n\n> Imported via MCP sync from ${url}`,
    });
  };

  return (
    <div data-testid="mcp-sync-mode">
      <button
        data-testid="btn-toggle-advanced"
        type="button"
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'none',
          border: 'none',
          color: C.muted,
          fontSize: '12px',
          fontWeight: 600,
          cursor: 'pointer',
          padding: '4px 0',
        }}
      >
        <span style={{ transition: 'transform 0.2s', transform: expanded ? 'rotate(90deg)' : 'none' }}>
          {'\u25B6'}
        </span>
        Advanced: MCP Server Sync
      </button>

      {expanded && (
        <div
          data-testid="mcp-expanded"
          style={{
            marginTop: '12px',
            padding: '16px',
            border: `1px solid ${C.border}`,
            borderRadius: '10px',
            background: C.surface,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 12px',
              borderRadius: '6px',
              background: C.amberDim,
              border: `1px solid ${C.amber}30`,
              marginBottom: '16px',
              fontSize: '11px',
              color: C.amber,
              fontWeight: 500,
            }}
          >
            Coming Soon — MCP sync is in preview. URL input is functional for testing.
          </div>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <input
              data-testid="input-mcp-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://mcp.example.com/server"
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: '12px',
                background: C.inputBg,
                border: `1px solid ${C.border}`,
                borderRadius: '8px',
                color: C.text,
                outline: 'none',
              }}
            />
            <button
              data-testid="btn-introspect"
              type="button"
              disabled={!url.trim()}
              onClick={handleIntrospect}
              style={{
                padding: '8px 16px',
                fontSize: '12px',
                fontWeight: 600,
                borderRadius: '8px',
                border: 'none',
                background: url.trim() ? C.accent : C.border,
                color: url.trim() ? '#fff' : C.dim,
                cursor: url.trim() ? 'pointer' : 'default',
                whiteSpace: 'nowrap',
              }}
            >
              Introspect
            </button>
          </div>

          {introspected && (
            <div data-testid="skill-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: C.muted, marginBottom: '4px' }}>
                Available Skills ({PLACEHOLDER_SKILLS.length})
              </div>
              {PLACEHOLDER_SKILLS.map((skill) => {
                const isSelected = selectedSkill?.name === skill.name;
                return (
                  <button
                    key={skill.name}
                    data-testid={`skill-option-${skill.name.toLowerCase().replace(/\s+/g, '-')}`}
                    type="button"
                    onClick={() => handleSelect(skill)}
                    style={{
                      padding: '10px 14px',
                      textAlign: 'left',
                      borderRadius: '8px',
                      border: `1px solid ${isSelected ? C.accent : C.border}`,
                      background: isSelected ? C.accentDim : 'transparent',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>{skill.name}</div>
                    <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>{skill.description}</div>
                  </button>
                );
              })}
            </div>
          )}

          {confirming && selectedSkill && (
            <div
              data-testid="confirm-import"
              style={{
                marginTop: '16px',
                padding: '12px 16px',
                borderRadius: '8px',
                border: `1px solid ${C.green}40`,
                background: C.greenDim,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '12px', color: C.text }}>
                Import <strong>{selectedSkill.name}</strong>?
              </span>
              <button
                data-testid="btn-confirm-import"
                type="button"
                onClick={handleConfirm}
                style={{
                  padding: '6px 16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: 'none',
                  background: C.green,
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                Confirm Import
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
