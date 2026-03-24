import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useT } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';
import { useAdminQueue, type ReviewQueueItem } from '../../hooks/useAdminQueue';
import { SubmissionCard } from '../../components/admin/SubmissionCard';
import { AuditLogPanel } from '../../components/admin/AuditLogPanel';
import { RequestChangesModal } from '../../components/admin/RequestChangesModal';
import { RejectModal } from '../../components/admin/RejectModal';
import { AdminConfirmDialog } from '../../components/admin/AdminConfirmDialog';

const QUEUE_LIST_WIDTH = '380px';

type DetailTab = 'details' | 'activity';

export function AdminQueueView() {
  const C = useT();
  const { user } = useAuth();
  const { data, loading, error, claim, decide } = useAdminQueue();
  const [searchParams, setSearchParams] = useSearchParams();

  const [selectedId, setSelectedId] = useState<string | null>(
    searchParams.get('id'),
  );
  const [activeTab, setActiveTab] = useState<DetailTab>('details');
  const [confirmApprove, setConfirmApprove] = useState<ReviewQueueItem | null>(null);
  const [requestChangesItem, setRequestChangesItem] = useState<ReviewQueueItem | null>(null);
  const [rejectItem, setRejectItem] = useState<ReviewQueueItem | null>(null);

  const items = data?.items ?? [];
  const selectedItem = items.find((i) => i.submission_id === selectedId) ?? null;

  const selectItem = useCallback(
    (id: string) => {
      setSelectedId(id);
      setSearchParams({ id }, { replace: true });
      setActiveTab('details');
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
          setConfirmApprove(selectedItem);
        }
      } else if ((e.key === 'r' || e.key === 'R') && selectedItem) {
        e.preventDefault();
        setRejectItem(selectedItem);
      } else if ((e.key === 'x' || e.key === 'X') && selectedItem) {
        e.preventDefault();
        setRequestChangesItem(selectedItem);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [items, selectedId, selectedItem, selectItem, user]);

  const handleApprove = async () => {
    if (!confirmApprove) return;
    await decide(confirmApprove.submission_id, 'approve');
    setConfirmApprove(null);
  };

  const handleReject = async (data: { reason: string; details: string }) => {
    if (!rejectItem) return;
    await decide(rejectItem.submission_id, 'reject', `${data.reason}: ${data.details}`);
    setRejectItem(null);
  };

  const handleRequestChanges = async (data: { flags: string[]; notes: string }) => {
    if (!requestChangesItem) return;
    const notes = `Flags: ${data.flags.join(', ')}\n${data.notes}`;
    await decide(requestChangesItem.submission_id, 'request_changes', notes);
    setRequestChangesItem(null);
  };

  const isSelfSubmission = selectedItem?.submitter_name === user?.name;

  const tabStyle = (tab: DetailTab): React.CSSProperties => ({
    padding: '8px 16px',
    fontSize: '13px',
    fontWeight: 600,
    border: 'none',
    borderBottom: activeTab === tab ? `2px solid ${C.accent}` : '2px solid transparent',
    background: 'transparent',
    color: activeTab === tab ? C.text : C.muted,
    cursor: 'pointer',
  });

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
            {items.map((item) => (
              <SubmissionCard
                key={item.submission_id}
                item={item}
                selected={item.submission_id === selectedId}
                onClick={() => selectItem(item.submission_id)}
              />
            ))}
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

                {/* Tabs */}
                <div
                  style={{
                    display: 'flex',
                    gap: '4px',
                    borderBottom: `1px solid ${C.border}`,
                    marginBottom: '20px',
                  }}
                >
                  <button style={tabStyle('details')} onClick={() => setActiveTab('details')}>
                    Details
                  </button>
                  <button style={tabStyle('activity')} onClick={() => setActiveTab('activity')}>
                    Activity
                  </button>
                </div>

                {activeTab === 'details' && (
                  <>
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
                  </>
                )}

                {activeTab === 'activity' && (
                  <AuditLogPanel displayId={selectedItem.display_id} />
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
                      setConfirmApprove(selectedItem);
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
                    onClick={() => setRejectItem(selectedItem)}
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
                    onClick={() => setRequestChangesItem(selectedItem)}
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

      {/* Approve Confirm Dialog */}
      {confirmApprove && (
        <AdminConfirmDialog
          title="Approve Submission"
          message={`Are you sure you want to approve "${confirmApprove.skill_name}"?`}
          confirmLabel="Approve"
          destructive={false}
          onConfirm={handleApprove}
          onCancel={() => setConfirmApprove(null)}
        />
      )}

      {/* Reject Modal */}
      <RejectModal
        open={rejectItem !== null}
        onClose={() => setRejectItem(null)}
        onSubmit={handleReject}
        submissionName={rejectItem?.skill_name ?? ''}
      />

      {/* Request Changes Modal */}
      <RequestChangesModal
        open={requestChangesItem !== null}
        onClose={() => setRequestChangesItem(null)}
        onSubmit={handleRequestChanges}
        submissionName={requestChangesItem?.skill_name ?? ''}
      />
    </div>
  );
}
