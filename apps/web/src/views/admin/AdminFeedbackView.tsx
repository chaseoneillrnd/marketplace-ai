import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { useAdminFeedback } from '../../hooks/useAdminFeedback';

const CATEGORIES = [
  { label: 'All', value: '' },
  { label: 'Feature Request', value: 'feature_request' },
  { label: 'Bug Report', value: 'bug_report' },
  { label: 'Praise', value: 'praise' },
  { label: 'Complaint', value: 'complaint' },
];

const SENTIMENTS = [
  { label: 'Positive', value: 'positive' },
  { label: 'Neutral', value: 'neutral' },
  { label: 'Critical', value: 'critical' },
];

function sentimentColor(sentiment: string, C: ReturnType<typeof useT>): { bg: string; text: string } {
  switch (sentiment) {
    case 'positive':
      return { bg: C.greenDim, text: C.green };
    case 'critical':
      return { bg: C.redDim, text: C.red };
    default:
      return { bg: C.border, text: C.muted };
  }
}

function statusBadgeColor(status: string, C: ReturnType<typeof useT>): { bg: string; text: string } {
  switch (status) {
    case 'open':
      return { bg: C.accentDim, text: C.accent };
    case 'archived':
      return { bg: C.border, text: C.dim };
    case 'resolved':
      return { bg: C.greenDim, text: C.green };
    default:
      return { bg: C.border, text: C.muted };
  }
}

export function AdminFeedbackView() {
  const C = useT();
  const [category, setCategory] = useState('');
  const [sentiment, setSentiment] = useState('');
  const [page, setPage] = useState(1);

  const { data, loading, archive } = useAdminFeedback({
    category: category || undefined,
    sentiment: sentiment || undefined,
    page,
  });

  const chipStyle = (active: boolean): React.CSSProperties => ({
    padding: '6px 14px',
    borderRadius: '99px',
    border: `1px solid ${active ? C.accent : C.border}`,
    background: active ? C.accentDim : 'transparent',
    color: active ? C.accent : C.muted,
    fontSize: '12px',
    fontWeight: 500,
    fontFamily: 'Outfit, sans-serif',
    cursor: 'pointer',
    transition: 'all 0.15s',
  });

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;

  return (
    <div data-testid="admin-feedback-view">
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px', color: C.text }}>Feedback</h1>

      {/* Category filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            style={chipStyle(category === cat.value)}
            onClick={() => { setCategory(cat.value); setPage(1); }}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Sentiment filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {SENTIMENTS.map((s) => {
          const active = sentiment === s.value;
          const sc = sentimentColor(s.value, C);
          return (
            <button
              key={s.value}
              style={{
                ...chipStyle(active),
                background: active ? sc.bg : 'transparent',
                color: active ? sc.text : C.muted,
                borderColor: active ? sc.text : C.border,
              }}
              onClick={() => { setSentiment(active ? '' : s.value); setPage(1); }}
            >
              {s.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {loading && !data ? (
        <p style={{ color: C.muted, fontSize: '13px' }}>Loading...</p>
      ) : !data || data.items.length === 0 ? (
        <p style={{ color: C.muted, fontSize: '13px' }}>No feedback found</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {data.items.map((item) => {
            const sc = sentimentColor(item.sentiment, C);
            const sb = statusBadgeColor(item.status, C);
            return (
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
                  {/* Sentiment label */}
                  <span
                    style={{
                      padding: '3px 10px',
                      borderRadius: '99px',
                      background: sc.bg,
                      color: sc.text,
                      fontSize: '11px',
                      fontWeight: 600,
                      fontFamily: 'Outfit, sans-serif',
                      textTransform: 'capitalize',
                    }}
                  >
                    {item.sentiment}
                  </span>

                  {/* Skill chip */}
                  {item.skill_name && (
                    <span
                      style={{
                        padding: '3px 10px',
                        borderRadius: '99px',
                        background: C.purpleDim,
                        color: C.purple,
                        fontSize: '11px',
                        fontWeight: 500,
                        fontFamily: 'Outfit, sans-serif',
                      }}
                    >
                      {item.skill_name}
                    </span>
                  )}

                  {/* Status badge */}
                  <span
                    style={{
                      padding: '3px 10px',
                      borderRadius: '99px',
                      background: sb.bg,
                      color: sb.text,
                      fontSize: '11px',
                      fontWeight: 500,
                      fontFamily: 'Outfit, sans-serif',
                      textTransform: 'capitalize',
                    }}
                  >
                    {item.status}
                  </span>

                  <span style={{ marginLeft: 'auto', color: C.dim, fontSize: '11px' }}>
                    {item.user_display_name}
                  </span>
                </div>

                {/* Body */}
                <div
                  style={{
                    background: C.codeBg,
                    borderRadius: '8px',
                    padding: '12px',
                    fontSize: '13px',
                    color: C.text,
                    lineHeight: 1.5,
                    marginBottom: '10px',
                  }}
                >
                  {item.body}
                </div>

                {/* Footer */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '12px', color: C.muted }}>
                    <span aria-label="upvotes" role="img">{'👍'}</span>{' '}
                    <span>{item.upvotes}</span>
                  </span>
                  {item.status !== 'archived' && (
                    <button
                      style={{
                        marginLeft: 'auto',
                        padding: '5px 12px',
                        borderRadius: '99px',
                        border: `1px solid ${C.border}`,
                        background: 'transparent',
                        color: C.muted,
                        fontSize: '11px',
                        fontWeight: 500,
                        cursor: 'pointer',
                        transition: 'all 0.15s',
                        fontFamily: 'Outfit, sans-serif',
                      }}
                      onClick={() => archive(item.id)}
                    >
                      Archive
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {data && totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px' }}>
          <button
            disabled={page <= 1}
            style={{
              ...chipStyle(false),
              opacity: page <= 1 ? 0.4 : 1,
              cursor: page <= 1 ? 'default' : 'pointer',
            }}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Prev
          </button>
          <span style={{ color: C.muted, fontSize: '12px', alignSelf: 'center' }}>
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            style={{
              ...chipStyle(false),
              opacity: page >= totalPages ? 0.4 : 1,
              cursor: page >= totalPages ? 'default' : 'pointer',
            }}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
