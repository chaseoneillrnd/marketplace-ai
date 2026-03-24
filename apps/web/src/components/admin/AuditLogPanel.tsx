import { useT } from '../../context/ThemeContext';
import { useAuditLog } from '../../hooks/useAuditLog';

interface AuditLogPanelProps {
  displayId: string | null;
}

const ACTION_COLORS: Record<string, string> = {
  submitted: '#4b7dff',
  approved: '#1fd49e',
  rejected: '#ef5060',
  changes_requested: '#f2a020',
  resubmitted: '#a78bfa',
  claimed: '#a78bfa',
  published: '#1fd49e',
};

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function AuditLogPanel({ displayId }: AuditLogPanelProps) {
  const C = useT();
  const { entries, loading, error } = useAuditLog(displayId);

  if (!displayId) return null;

  if (loading) {
    return (
      <div
        data-testid="audit-log-loading"
        style={{ color: C.muted, fontSize: '13px', padding: '16px 0', textAlign: 'center' }}
      >
        Loading activity...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ color: C.red, fontSize: '13px', padding: '16px 0' }}>
        {error}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div
        data-testid="audit-log-empty"
        style={{ color: C.muted, fontSize: '13px', padding: '16px 0', textAlign: 'center' }}
      >
        No activity yet
      </div>
    );
  }

  return (
    <div data-testid="audit-log-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
      {entries.map((entry, idx) => {
        const dotColor = ACTION_COLORS[entry.action] ?? C.muted;
        const isLast = idx === entries.length - 1;

        return (
          <div
            key={entry.id}
            data-testid="audit-log-entry"
            style={{ display: 'flex', gap: '12px', minHeight: '48px' }}
          >
            {/* Timeline column */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                width: '20px',
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: dotColor,
                  marginTop: '4px',
                  flexShrink: 0,
                }}
              />
              {!isLast && (
                <div
                  style={{
                    width: '2px',
                    flex: 1,
                    background: C.border,
                    marginTop: '4px',
                  }}
                />
              )}
            </div>

            {/* Content column */}
            <div style={{ flex: 1, paddingBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '2px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
                  {entry.actor_name}
                </span>
                <span style={{ fontSize: '12px', color: C.muted }}>
                  {entry.action.replace(/_/g, ' ')}
                </span>
              </div>
              {entry.from_status && entry.to_status && (
                <div style={{ fontSize: '11px', color: C.dim, marginBottom: '2px' }}>
                  {entry.from_status.replace(/_/g, ' ')} &rarr; {entry.to_status.replace(/_/g, ' ')}
                </div>
              )}
              {entry.notes && (
                <div
                  style={{
                    fontSize: '12px',
                    color: C.muted,
                    marginTop: '4px',
                    padding: '8px 12px',
                    background: C.codeBg,
                    borderRadius: '8px',
                    borderLeft: `3px solid ${dotColor}`,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {entry.notes}
                </div>
              )}
              <div style={{ fontSize: '11px', color: C.dim, marginTop: '4px' }}>
                {formatTimestamp(entry.created_at)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
