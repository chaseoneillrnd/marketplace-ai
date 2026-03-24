import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { useAdminRoadmap, type RoadmapItem } from '../../hooks/useAdminRoadmap';

const COLUMNS = [
  { key: 'planned', label: 'PLANNED' },
  { key: 'in_progress', label: 'IN PROGRESS' },
  { key: 'shipped', label: 'SHIPPED' },
  { key: 'cancelled', label: 'CANCELLED' },
] as const;

function columnColor(key: string, C: ReturnType<typeof useT>): string {
  switch (key) {
    case 'planned': return C.muted;
    case 'in_progress': return C.accent;
    case 'shipped': return C.green;
    case 'cancelled': return C.dim;
    default: return C.muted;
  }
}

export function AdminRoadmapView() {
  const C = useT();
  const { items, loading, createItem, shipItem } = useAdminRoadmap();
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newBody, setNewBody] = useState('');
  const [shipDialogId, setShipDialogId] = useState<string | null>(null);
  const [versionTag, setVersionTag] = useState('');
  const [changelogBody, setChangelogBody] = useState('');

  const grouped: Record<string, RoadmapItem[]> = {
    planned: [],
    in_progress: [],
    shipped: [],
    cancelled: [],
  };
  for (const item of items) {
    if (grouped[item.status]) {
      grouped[item.status].push(item);
    }
  }

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    await createItem(newTitle.trim(), newBody.trim());
    setNewTitle('');
    setNewBody('');
    setShowNewForm(false);
  };

  const handleShip = async () => {
    if (!shipDialogId || !versionTag.trim()) return;
    await shipItem(shipDialogId, versionTag.trim(), changelogBody.trim());
    setShipDialogId(null);
    setVersionTag('');
    setChangelogBody('');
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 10px',
    borderRadius: '8px',
    border: `1px solid ${C.border}`,
    background: C.inputBg,
    color: C.text,
    fontSize: '12px',
    fontFamily: 'Outfit, sans-serif',
    outline: 'none',
    boxSizing: 'border-box',
  };

  return (
    <div data-testid="admin-roadmap-view">
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px', color: C.text }}>Roadmap</h1>

      {loading && items.length === 0 ? (
        <p style={{ color: C.muted, fontSize: '13px' }}>Loading...</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
          {COLUMNS.map((col) => {
            const colItems = grouped[col.key] || [];
            const color = columnColor(col.key, C);
            return (
              <div key={col.key} style={{ minWidth: 0 }}>
                {/* Column header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      fontFamily: 'Outfit, sans-serif',
                      letterSpacing: '0.8px',
                      color,
                      textTransform: 'uppercase',
                    }}
                  >
                    {col.label}
                  </span>
                  <span
                    data-testid="column-count"
                    style={{
                      fontSize: '10px',
                      fontWeight: 600,
                      fontFamily: 'Outfit, sans-serif',
                      padding: '2px 7px',
                      borderRadius: '99px',
                      background: C.border,
                      color: C.muted,
                    }}
                  >
                    {colItems.length}
                  </span>
                </div>

                {/* New Item button (Planned column only) */}
                {col.key === 'planned' && !showNewForm && (
                  <button
                    onClick={() => setShowNewForm(true)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '12px',
                      border: `1px dashed ${C.border}`,
                      background: 'transparent',
                      color: C.muted,
                      fontSize: '12px',
                      fontWeight: 500,
                      cursor: 'pointer',
                      marginBottom: '10px',
                      fontFamily: 'Outfit, sans-serif',
                      transition: 'all 0.15s',
                    }}
                  >
                    + New Item
                  </button>
                )}

                {/* Inline new item form */}
                {col.key === 'planned' && showNewForm && (
                  <div
                    style={{
                      background: C.surface,
                      border: `1px solid ${C.borderHi}`,
                      borderRadius: '12px',
                      padding: '12px',
                      marginBottom: '10px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <input
                      placeholder="Title"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      style={inputStyle}
                    />
                    <textarea
                      placeholder="Description"
                      value={newBody}
                      onChange={(e) => setNewBody(e.target.value)}
                      rows={3}
                      style={{ ...inputStyle, resize: 'vertical' }}
                    />
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={handleCreate}
                        style={{
                          padding: '6px 14px',
                          borderRadius: '99px',
                          border: 'none',
                          background: C.green,
                          color: '#fff',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          fontFamily: 'Outfit, sans-serif',
                        }}
                      >
                        Create
                      </button>
                      <button
                        onClick={() => { setShowNewForm(false); setNewTitle(''); setNewBody(''); }}
                        style={{
                          padding: '6px 14px',
                          borderRadius: '99px',
                          border: `1px solid ${C.border}`,
                          background: 'transparent',
                          color: C.muted,
                          fontSize: '11px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          fontFamily: 'Outfit, sans-serif',
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Cards */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {colItems.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        background: C.surface,
                        border: `1px solid ${C.border}`,
                        borderRadius: '12px',
                        padding: '16px',
                        transition: 'border-color 0.15s',
                      }}
                    >
                      <div style={{ fontSize: '13px', fontWeight: 600, color: C.text, marginBottom: '6px' }}>
                        {item.title}
                      </div>
                      <div style={{ fontSize: '12px', color: C.muted, lineHeight: 1.4, marginBottom: '8px' }}>
                        {item.body}
                      </div>
                      {item.version_tag && (
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            borderRadius: '99px',
                            background: C.greenDim,
                            color: C.green,
                            fontSize: '10px',
                            fontWeight: 600,
                            fontFamily: 'Outfit, sans-serif',
                            marginBottom: '6px',
                          }}
                        >
                          {item.version_tag}
                        </span>
                      )}
                      {col.key === 'in_progress' && shipDialogId !== item.id && (
                        <button
                          onClick={() => setShipDialogId(item.id)}
                          style={{
                            display: 'block',
                            marginTop: '4px',
                            padding: '5px 12px',
                            borderRadius: '99px',
                            border: 'none',
                            background: C.greenDim,
                            color: C.green,
                            fontSize: '11px',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontFamily: 'Outfit, sans-serif',
                            transition: 'all 0.15s',
                          }}
                        >
                          Mark as Shipped
                        </button>
                      )}
                      {col.key === 'in_progress' && shipDialogId === item.id && (
                        <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <input
                            placeholder="Version tag (e.g. v1.3.0)"
                            value={versionTag}
                            onChange={(e) => setVersionTag(e.target.value)}
                            style={inputStyle}
                          />
                          <textarea
                            placeholder="Changelog entry"
                            value={changelogBody}
                            onChange={(e) => setChangelogBody(e.target.value)}
                            rows={2}
                            style={{ ...inputStyle, resize: 'vertical' }}
                          />
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button
                              onClick={handleShip}
                              style={{
                                padding: '5px 12px',
                                borderRadius: '99px',
                                border: 'none',
                                background: C.green,
                                color: '#fff',
                                fontSize: '11px',
                                fontWeight: 600,
                                cursor: 'pointer',
                                fontFamily: 'Outfit, sans-serif',
                              }}
                            >
                              Ship
                            </button>
                            <button
                              onClick={() => { setShipDialogId(null); setVersionTag(''); setChangelogBody(''); }}
                              style={{
                                padding: '5px 12px',
                                borderRadius: '99px',
                                border: `1px solid ${C.border}`,
                                background: 'transparent',
                                color: C.muted,
                                fontSize: '11px',
                                fontWeight: 500,
                                cursor: 'pointer',
                                fontFamily: 'Outfit, sans-serif',
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
