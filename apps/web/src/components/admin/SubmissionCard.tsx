import { useT } from '../../context/ThemeContext';
import { type ReviewQueueItem } from '../../hooks/useAdminQueue';
import { RevisionBadge } from './RevisionBadge';

interface SubmissionCardProps {
  item: ReviewQueueItem;
  selected: boolean;
  onClick: () => void;
}

const STATUS_COLORS: Record<string, { color: string; bg: string; label: string }> = {
  pending_review: { color: '#4b7dff', bg: 'rgba(75,125,255,0.12)', label: 'Pending Review' },
  in_review: { color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', label: 'In Review' },
  changes_requested: { color: '#f2a020', bg: 'rgba(242,160,32,0.10)', label: 'Changes Requested' },
  approved: { color: '#1fd49e', bg: 'rgba(31,212,158,0.10)', label: 'Approved' },
  rejected: { color: '#ef5060', bg: 'rgba(239,80,96,0.10)', label: 'Rejected' },
  published: { color: '#1fd49e', bg: 'rgba(31,212,158,0.10)', label: 'Published' },
};

function getSLAInfo(waitTimeHours: number): { label: string; color: string; bg: string } {
  if (waitTimeHours > 48) return { label: 'SLA breached', color: '#ef5060', bg: 'rgba(239,80,96,0.10)' };
  if (waitTimeHours >= 24) return { label: 'SLA at risk', color: '#f2a020', bg: 'rgba(242,160,32,0.10)' };
  return { label: formatWaitTime(waitTimeHours), color: '#1fd49e', bg: 'rgba(31,212,158,0.10)' };
}

function formatWaitTime(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)}m ago`;
  if (hours < 24) return `${Math.round(hours)}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function SubmissionCard({ item, selected, onClick }: SubmissionCardProps) {
  const C = useT();
  const sla = getSLAInfo(item.wait_time_hours);
  const status = STATUS_COLORS[item.status ?? 'pending_review'] ?? STATUS_COLORS.pending_review;

  return (
    <button
      data-testid="submission-card"
      onClick={onClick}
      style={{
        display: 'block',
        width: '100%',
        padding: '14px 16px',
        background: selected ? C.accentDim : 'transparent',
        border: 'none',
        borderBottom: `1px solid ${C.border}`,
        cursor: 'pointer',
        textAlign: 'left',
      }}
    >
      {/* Row 1: Skill name + revision badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
        <span
          style={{
            fontSize: '14px',
            fontWeight: 600,
            fontFamily: 'Outfit, sans-serif',
            color: C.text,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {item.skill_name}
        </span>
        <RevisionBadge revisionNumber={item.revision_number ?? 1} />
      </div>

      {/* Row 2: Submitter + division */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
        <span style={{ fontSize: '12px', fontWeight: 400, color: C.muted }}>
          {item.submitter_name ?? 'Unknown'}
        </span>
        {item.divisions.length > 0 && (
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
            {item.divisions[0]}
          </span>
        )}
      </div>

      {/* Row 3: Status + category + SLA */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
        <span
          data-testid="status-badge"
          style={{
            fontSize: '10px',
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: '99px',
            background: status.bg,
            color: status.color,
          }}
        >
          {status.label}
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
        <span
          data-testid="sla-timer"
          style={{
            fontSize: '10px',
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: '99px',
            background: sla.bg,
            color: sla.color,
            marginLeft: 'auto',
          }}
        >
          {sla.label}
        </span>
      </div>
    </button>
  );
}
