import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useT } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';
import { useAdminQueue, type ReviewQueueItem } from '../../hooks/useAdminQueue';
import { AdminConfirmDialog } from '../../components/admin/AdminConfirmDialog';

const QUEUE_LIST_WIDTH = '380px';

function getSLABadge(waitTimeHours: number): { label: string; color: string; bg: string } | null {
  if (waitTimeHours > 48) return { label: 'SLA breached', color: '#ef5060', bg: 'rgba(239,80,96,0.10)' };
  if (waitTimeHours >= 24) return { label: 'SLA at risk', color: '#f2a020', bg: 'rgba(242,160,32,0.10)' };
  return null;
}

export function AdminQueueView() {
  const C = useT();
  const { user } = useAuth();
  const { data, loading, error, claim, decide } = useAdminQueue();
  const [searchParams, setSearchParams] = useSearchParams();

  const [selectedId, setSelectedId] = useState<string | null>(
    searchParams.get('id'),
  );
  const [confirmAction, setConfirmAction] = useState<{
    type: 'approve' | 'reject' | 'request_changes';
    item: ReviewQueueItem;
  } | null>(null);
  const [notesText, setNotesText] = useState('');

  const items = data?.items ?? [];
  const selectedItem = items.find((i) => i.submission_id === selectedId) ?? null;

  const selectItem = useCallback(
    (id: string) => {
      setSelectedId(id);
      setSearchParams({ id }, { replace: true });
    },
    [setSearchParams],
  );

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      const currentIndex = items.findIndex((i) => i.submission_id === selectedId);

      if (e.key === 'j' || e.key === 'J') {
        e.preventDefault();
        const next = Math.min(currentIndex + 1, items.length - 1);
        if (items[next]) selectItem(items[next].submission_id);
      } else if (e.key === 'k' || e.key === 'K') {
        e.preventDefault();
        const prev = Math.max(currentIndex - 1, 0);
        if (items[prev]) selectItem(items[prev].submission_id);
      } else if ((e.key === 'a' || e.key === 'A') && selectedItem) {
        e.preventDefault();
        const isSelfSubmission = selectedItem.submitter_name === user?.name;
        if (!isSelfSubmission) {
          setConfirmAction({ type: 'approve', item: selectedItem });
        }
      } else if ((e.key === 'r' || e.key === 'R') && selectedItem) {
        e.preventDefault();
        setConfirmAction({ type: 'reject', item: selectedItem });
      } else if ((e.key === 'x' || e.key === 'X') && selectedItem) {
        e.preventDefault();
        setConfirmAction({ type: 'request_changes', item: selectedItem });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [items, selectedId, selectedItem, selectItem, user]);

  const handleDecision = async (type: 'approve' | 'reject' | 'request_changes') => {
    if (!confirmAction) return;
    await decide(confirmAction.item.submission_id, type, notesText);
    setConfirmAction(null);
    setNotesText('');
  };

  const isSelfSubmission = selectedItem?.submitter_name === user?.name;

  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px', color: C.text }}>
        Review Queue
      </h1>

      {loading && (
        <p style={{ color: C.muted, fontSize: '14px' }}>Loading queue...</p>
      )}

      {error && (
        <p style={{ color: C.red, fontSize: '14px' }}>{error}</p>
      )}

      {!loading && !error && items.length === 0 && (
        <p style={{ color: C.muted, fontSize: '14px' }}>No items in the review queue.</p>
      )}

      {!loading && items.length > 0 && (
        <div style={{ display: 'flex', gap: '1px', background: C.border, borderRadius: '12px', overflow: 'hidden', minHeight: '500px' }}>
          {/* Queue List */}
          <div
            style={{
              width: QUEUE_LIST_WIDTH,
              flexShrink: 0,
              background: C.surface,
              overflowY: 'auto',
              maxHeight: '70vh',
            }}
          >
            {items.map((item) => {
              const isSelected = item.submission_id === selectedId;
              const slaBadge = getSLABadge(item.wait_time_hours);
              return (
                <button
                  key={item.submission_id}
                  onClick={() => selectItem(item.submission_id)}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '14px 16px',
                    background: isSelected ? C.accentDim : 'transparent',
                    border: 'none',
                    borderBottom: `1px solid ${C.border}`,
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'Outfit, sans-serif', color: C.text }}>
                      {item.skill_name}
                    </span>
                    {slaBadge && (
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: '99px',
                          background: slaBadge.bg,
                          color: slaBadge.color,
                        }}
                      >
                        {slaBadge.label}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 400, color: C.muted }}>
                      {item.submitter_name ?? 'Unknown'}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        padding: '2px 8px',
                        borderRadius: '99px',
                        background: C.purpleDim,
                        color: C.purple,
                        fontWeight: 600,
                      }}
                    >
                      {item.category}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Detail Panel */}
          <div style={{ flex: 1, background: C.surface, padding: '24px', overflowY: 'auto' }}>
            {!selectedItem ? (
              <div style={{ color: C.muted, fontSize: '14px', textAlign: 'center', marginTop: '80px' }}>
                Select an item from the queue to review
              </div>
            ) : (
              <div>
                <h2
                  style={{
                    fontSize: '22px',
                    fontWeight: 700,
                    fontFamily: 'Outfit, sans-serif',
                    color: C.text,
                    margin: '0 0 6px 0',
                  }}
                >
                  {selectedItem.skill_name}
                </h2>
                <p style={{ fontSize: '13px', color: C.muted, margin: '0 0 20px 0' }}>
                  {selectedItem.short_desc}
                </p>

                {/* Content Preview */}
                <div
                  style={{
                    background: C.codeBg,
                    padding: '16px',
                    borderRadius: '10px',
                    fontFamily: 'monospace',
                    fontSize: '13px',
                    color: C.text,
                    marginBottom: '20px',
                    whiteSpace: 'pre-wrap',
                    overflowX: 'auto',
                  }}
                >
                  {selectedItem.content_preview}
                </div>

                {/* Gate Results */}
                <div style={{ marginBottom: '20px' }}>
                  <div
                    style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.9px',
                      color: C.dim,
                      marginBottom: '8px',
                    }}
                  >
                    Gate Results
                  </div>
                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <div
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        background: selectedItem.gate1_passed ? C.greenDim : C.redDim,
                        color: selectedItem.gate1_passed ? C.green : C.red,
                        fontSize: '12px',
                        fontWeight: 600,
                      }}
                    >
                      Gate 1: {selectedItem.gate1_passed ? 'Passed' : 'Failed'}
                    </div>
                    {selectedItem.gate2_score !== null && (
                      <div
                        style={{
                          padding: '8px 14px',
                          borderRadius: '8px',
                          background: C.accentDim,
                          color: C.accent,
                          fontSize: '12px',
                          fontWeight: 600,
                        }}
                      >
                        Gate 2: {selectedItem.gate2_score}/100
                      </div>
                    )}
                  </div>
                  {selectedItem.gate2_summary && (
                    <p style={{ fontSize: '12px', color: C.muted, marginTop: '8px' }}>
                      {selectedItem.gate2_summary}
                    </p>
                  )}
                </div>

                {/* Divisions */}
                {selectedItem.divisions.length > 0 && (
                  <div style={{ marginBottom: '20px' }}>
                    <div
                      style={{
                        fontSize: '11px',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.9px',
                        color: C.dim,
                        marginBottom: '8px',
                      }}
                    >
                      Divisions
                    </div>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {selectedItem.divisions.map((div) => (
                        <span
                          key={div}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '99px',
                            background: C.purpleDim,
                            color: C.purple,
                            fontSize: '11px',
                            fontWeight: 600,
                          }}
                        >
                          {div}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div
                  style={{
                    display: 'flex',
                    gap: '10px',
                    paddingTop: '16px',
                    borderTop: `1px solid ${C.border}`,
                  }}
                >
                  <button
                    aria-disabled={isSelfSubmission ? 'true' : undefined}
                    title={isSelfSubmission ? 'Cannot approve your own submission' : undefined}
                    onClick={() => {
                      if (isSelfSubmission) return;
                      setConfirmAction({ type: 'approve', item: selectedItem });
                    }}
                    style={{
                      padding: '10px 20px',
                      borderRadius: '8px',
                      border: 'none',
                      background: isSelfSubmission ? C.dim : C.green,
                      color: '#fff',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: isSelfSubmission ? 'not-allowed' : 'pointer',
                      opacity: isSelfSubmission ? 0.5 : 1,
                    }}
                  >
                    Approve
                  </button>
                  <button
                    onClick={() =>
                      setConfirmAction({ type: 'reject', item: selectedItem })
                    }
                    style={{
                      padding: '10px 20px',
                      borderRadius: '8px',
                      border: 'none',
                      background: C.red,
                      color: '#fff',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Reject
                  </button>
                  <button
                    onClick={() =>
                      setConfirmAction({ type: 'request_changes', item: selectedItem })
                    }
                    style={{
                      padding: '10px 20px',
                      borderRadius: '8px',
                      border: 'none',
                      background: C.amber,
                      color: '#fff',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Request Changes
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confirm Dialog */}
      {confirmAction && (
        <AdminConfirmDialog
          title={
            confirmAction.type === 'approve'
              ? 'Approve Submission'
              : confirmAction.type === 'reject'
                ? 'Reject Submission'
                : 'Request Changes'
          }
          message={`Are you sure you want to ${confirmAction.type.replace('_', ' ')} "${confirmAction.item.skill_name}"?`}
          confirmLabel={
            confirmAction.type === 'approve'
              ? 'Approve'
              : confirmAction.type === 'reject'
                ? 'Reject'
                : 'Request Changes'
          }
          destructive={confirmAction.type === 'reject'}
          onConfirm={() => handleDecision(confirmAction.type)}
          onCancel={() => {
            setConfirmAction(null);
            setNotesText('');
          }}
        />
      )}
    </div>
  );
}
