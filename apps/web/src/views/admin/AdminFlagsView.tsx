import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { useAdminFlags, type AdminFlag } from '../../hooks/useAdminFlags';

const DIVISIONS = [
  'engineering-org',
  'product-org',
  'data-science-org',
  'security-org',
  'finance-legal',
  'people-hr',
  'operations',
  'executive-office',
  'sales-marketing',
  'customer-success',
];

type OverrideState = 'inherit' | 'enable' | 'disable';

function domainPrefix(key: string): string {
  const dot = key.indexOf('.');
  return dot > 0 ? key.substring(0, dot) : '';
}

function domainColor(prefix: string, C: ReturnType<typeof useT>): string {
  switch (prefix) {
    case 'hitl':
      return C.purple;
    case 'submission':
      return C.accent;
    case 'docs':
      return C.green;
    default:
      return C.muted;
  }
}

function domainBgColor(prefix: string, C: ReturnType<typeof useT>): string {
  switch (prefix) {
    case 'hitl':
      return C.purpleDim;
    case 'submission':
      return C.accentDim;
    case 'docs':
      return C.greenDim;
    default:
      return C.border;
  }
}

export function AdminFlagsView() {
  const C = useT();
  const { flags, loading, createFlag, updateFlag, deleteFlag } = useAdminFlags();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newEnabled, setNewEnabled] = useState(true);

  const selectedFlag = flags.find((f) => f.key === selectedKey) ?? null;

  const handleToggle = async (flag: AdminFlag) => {
    await updateFlag(flag.key, { enabled: !flag.enabled });
  };

  const handleCreate = async () => {
    if (!newKey.trim()) return;
    await createFlag({ key: newKey.trim(), enabled: newEnabled, description: newDescription || undefined });
    setNewKey('');
    setNewDescription('');
    setNewEnabled(true);
    setShowCreate(false);
  };

  const handleDelete = async (key: string) => {
    await deleteFlag(key);
    if (selectedKey === key) setSelectedKey(null);
  };

  const handleOverrideChange = async (flag: AdminFlag, division: string, state: OverrideState) => {
    const overrides = { ...(flag.division_overrides ?? {}) };
    if (state === 'inherit') {
      delete overrides[division];
    } else {
      overrides[division] = state === 'enable';
    }
    await updateFlag(flag.key, { division_overrides: Object.keys(overrides).length > 0 ? overrides : null });
  };

  const getOverrideState = (flag: AdminFlag, division: string): OverrideState => {
    if (!flag.division_overrides || !(division in flag.division_overrides)) return 'inherit';
    return flag.division_overrides[division] ? 'enable' : 'disable';
  };

  const pillStyle = (enabled: boolean): React.CSSProperties => ({
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: '99px',
    fontSize: '11px',
    fontWeight: 600,
    fontFamily: 'Outfit, sans-serif',
    background: enabled ? C.greenDim : C.redDim,
    color: enabled ? C.green : C.red,
    cursor: 'pointer',
    border: 'none',
    transition: 'all 0.15s',
  });

  const inputStyle: React.CSSProperties = {
    background: C.inputBg,
    border: `1px solid ${C.border}`,
    borderRadius: '8px',
    padding: '8px 12px',
    color: C.text,
    fontSize: '13px',
    fontFamily: 'Outfit, sans-serif',
    outline: 'none',
    width: '100%',
  };

  const btnStyle: React.CSSProperties = {
    padding: '8px 16px',
    borderRadius: '8px',
    border: `1px solid ${C.accent}`,
    background: C.accentDim,
    color: C.accent,
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'Outfit, sans-serif',
    cursor: 'pointer',
    transition: 'all 0.15s',
  };

  const triStateBtn = (active: boolean, color: string, bgColor: string): React.CSSProperties => ({
    padding: '3px 10px',
    borderRadius: '99px',
    border: active ? `1px solid ${color}` : `1px solid ${C.border}`,
    background: active ? bgColor : 'transparent',
    color: active ? color : C.dim,
    fontSize: '10px',
    fontWeight: 500,
    fontFamily: 'Outfit, sans-serif',
    cursor: 'pointer',
    transition: 'all 0.15s',
  });

  return (
    <div data-testid="admin-flags-view">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: C.text }}>Feature Flags</h1>
        <button style={btnStyle} onClick={() => setShowCreate(true)} data-testid="create-flag-btn">
          + Create Flag
        </button>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div
          data-testid="create-flag-modal"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowCreate(false); }}
        >
          <div
            style={{
              background: C.surface,
              border: `1px solid ${C.border}`,
              borderRadius: '12px',
              padding: '24px',
              width: '420px',
              maxWidth: '90vw',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: C.text, marginBottom: '16px' }}>Create Feature Flag</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <input
                style={inputStyle}
                placeholder="Flag key (e.g. submission.new_feature)"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                data-testid="create-flag-key"
              />
              <input
                style={inputStyle}
                placeholder="Description"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                data-testid="create-flag-description"
              />
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: C.muted, fontSize: '13px' }}>
                <input
                  type="checkbox"
                  checked={newEnabled}
                  onChange={(e) => setNewEnabled(e.target.checked)}
                />
                Enabled by default
              </label>
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button
                  style={{ ...btnStyle, background: 'transparent', borderColor: C.border, color: C.muted }}
                  onClick={() => setShowCreate(false)}
                >
                  Cancel
                </button>
                <button style={btnStyle} onClick={handleCreate} data-testid="create-flag-submit">
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && flags.length === 0 ? (
        <p style={{ color: C.muted, fontSize: '13px' }}>Loading...</p>
      ) : flags.length === 0 ? (
        <p style={{ color: C.muted, fontSize: '13px' }}>No feature flags found</p>
      ) : (
        <div style={{ display: 'flex', gap: '20px' }}>
          {/* Flag list */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {flags.map((flag) => {
              const prefix = domainPrefix(flag.key);
              const isSelected = selectedKey === flag.key;
              const overrideCount = flag.division_overrides ? Object.keys(flag.division_overrides).length : 0;

              return (
                <div
                  key={flag.key}
                  data-testid={`flag-row-${flag.key}`}
                  onClick={() => setSelectedKey(isSelected ? null : flag.key)}
                  style={{
                    background: isSelected ? C.surfaceHi : C.surface,
                    border: `1px solid ${isSelected ? C.accent : C.border}`,
                    borderRadius: '10px',
                    padding: '14px 16px',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    {/* Domain prefix badge */}
                    {prefix && (
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '99px',
                          background: domainBgColor(prefix, C),
                          color: domainColor(prefix, C),
                          fontSize: '10px',
                          fontWeight: 600,
                          fontFamily: 'JetBrains Mono, monospace',
                        }}
                      >
                        {prefix}
                      </span>
                    )}
                    <span
                      style={{
                        fontSize: '13px',
                        fontWeight: 600,
                        color: C.text,
                        fontFamily: 'JetBrains Mono, monospace',
                      }}
                    >
                      {flag.key}
                    </span>

                    <span style={{ marginLeft: 'auto' }}>
                      <button
                        style={pillStyle(flag.enabled)}
                        onClick={(e) => { e.stopPropagation(); handleToggle(flag); }}
                        data-testid={`flag-toggle-${flag.key}`}
                        aria-label={`Toggle ${flag.key}`}
                      >
                        {flag.enabled ? 'ON' : 'OFF'}
                      </button>
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {flag.description && (
                      <span style={{ fontSize: '12px', color: C.muted }}>{flag.description}</span>
                    )}

                    {/* Division override dots */}
                    {overrideCount > 0 && (
                      <span style={{ marginLeft: 'auto', display: 'flex', gap: '3px' }}>
                        {Object.entries(flag.division_overrides!).map(([div, enabled]) => (
                          <span
                            key={div}
                            title={`${div}: ${enabled ? 'enabled' : 'disabled'}`}
                            style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              background: enabled ? C.green : C.red,
                              display: 'inline-block',
                            }}
                          />
                        ))}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Detail panel */}
          {selectedFlag && (
            <div
              data-testid="flag-detail-panel"
              style={{
                width: '380px',
                minWidth: '320px',
                background: C.surface,
                border: `1px solid ${C.border}`,
                borderRadius: '12px',
                padding: '20px',
                alignSelf: 'flex-start',
                position: 'sticky',
                top: '80px',
              }}
            >
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: C.text, marginBottom: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
                {selectedFlag.key}
              </h2>
              <p style={{ fontSize: '12px', color: C.muted, marginBottom: '16px' }}>
                {selectedFlag.description ?? 'No description'}
              </p>

              {/* Global toggle */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                <span style={{ fontSize: '13px', color: C.text, fontWeight: 500 }}>Global:</span>
                <button
                  style={pillStyle(selectedFlag.enabled)}
                  onClick={() => handleToggle(selectedFlag)}
                  data-testid="detail-toggle"
                >
                  {selectedFlag.enabled ? 'ON' : 'OFF'}
                </button>
              </div>

              {/* Division overrides */}
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ fontSize: '12px', fontWeight: 600, color: C.dim, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
                  Division Overrides
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {DIVISIONS.map((div) => {
                    const state = getOverrideState(selectedFlag, div);
                    return (
                      <div key={div} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '11px', color: C.muted, width: '130px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {div}
                        </span>
                        <button
                          style={triStateBtn(state === 'inherit', C.muted, C.border)}
                          onClick={() => handleOverrideChange(selectedFlag, div, 'inherit')}
                        >
                          Inherit
                        </button>
                        <button
                          style={triStateBtn(state === 'enable', C.green, C.greenDim)}
                          onClick={() => handleOverrideChange(selectedFlag, div, 'enable')}
                        >
                          Enable
                        </button>
                        <button
                          style={triStateBtn(state === 'disable', C.red, C.redDim)}
                          onClick={() => handleOverrideChange(selectedFlag, div, 'disable')}
                        >
                          Disable
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Delete button */}
              <button
                style={{
                  ...btnStyle,
                  background: C.redDim,
                  borderColor: C.red,
                  color: C.red,
                  width: '100%',
                }}
                onClick={() => handleDelete(selectedFlag.key)}
                data-testid="delete-flag-btn"
              >
                Delete Flag
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
