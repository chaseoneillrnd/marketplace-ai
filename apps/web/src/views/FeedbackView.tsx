import { useState } from 'react';
import { useT } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';
import { useFeedback } from '../hooks/useFeedback';

const CATEGORY_TABS = [
  { label: 'All', value: undefined },
  { label: 'Feature Requests', value: 'feature_request' },
  { label: 'Bug Reports', value: 'bug_report' },
  { label: 'Praise', value: 'praise' },
  { label: 'Complaints', value: 'complaint' },
] as const;

const CATEGORY_LABELS: Record<string, string> = {
  feature_request: 'Feature Request',
  bug_report: 'Bug Report',
  praise: 'Praise',
  complaint: 'Complaint',
};

const CATEGORY_COLORS: Record<string, string> = {
  feature_request: '#4b7dff',
  bug_report: '#ef4444',
  praise: '#22c55e',
  complaint: '#f97316',
};

export function FeedbackView() {
  const C = useT();
  const { isAuthenticated } = useAuth();
  const { items, total, page, loading, error, submitFeedback, upvote, setPage, setCategory } =
    useFeedback();

  const [activeTab, setActiveTab] = useState<string | undefined>(undefined);
  const [formCategory, setFormCategory] = useState('feature_request');
  const [formBody, setFormBody] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleTabChange = (value: string | undefined) => {
    setActiveTab(value);
    setCategory(value);
    setPage(1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formBody.trim().length < 20) {
      setSubmitError('Body must be at least 20 characters.');
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);
    try {
      await submitFeedback(formCategory, formBody.trim());
      setFormBody('');
      setSubmitSuccess(true);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit feedback.');
    } finally {
      setSubmitting(false);
    }
  };

  const perPage = 20;
  const totalPages = Math.ceil(total / perPage);

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '32px 24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700, color: C.text, margin: '0 0 6px' }}>
          Feedback
        </h1>
        <p style={{ fontSize: '13px', color: C.muted, margin: 0 }}>
          Share ideas, report bugs, or tell us what you love. Your feedback shapes SkillHub.
        </p>
      </div>

      {/* Submit form */}
      <div
        style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '24px',
        }}
      >
        <h2 style={{ fontSize: '13px', fontWeight: 600, color: C.text, margin: '0 0 14px' }}>
          Submit Feedback
        </h2>
        {isAuthenticated ? (
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '12px', flexWrap: 'wrap' }}>
              <select
                value={formCategory}
                onChange={(e) => setFormCategory(e.target.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: `1px solid ${C.border}`,
                  background: C.bg,
                  color: C.text,
                  fontSize: '13px',
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="feature_request">Feature Request</option>
                <option value="bug_report">Bug Report</option>
                <option value="praise">Praise</option>
                <option value="complaint">Complaint</option>
              </select>
            </div>
            <textarea
              value={formBody}
              onChange={(e) => setFormBody(e.target.value)}
              placeholder="Describe your feedback (min 20 characters)..."
              rows={4}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '8px',
                border: `1px solid ${C.border}`,
                background: C.bg,
                color: C.text,
                fontSize: '13px',
                resize: 'vertical',
                outline: 'none',
                fontFamily: 'inherit',
                marginBottom: '12px',
              }}
            />
            {submitError && (
              <p style={{ fontSize: '12px', color: C.red, margin: '0 0 10px' }}>{submitError}</p>
            )}
            {submitSuccess && (
              <p style={{ fontSize: '12px', color: '#22c55e', margin: '0 0 10px' }}>
                Feedback submitted — thank you!
              </p>
            )}
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: '8px 20px',
                borderRadius: '8px',
                border: 'none',
                background: submitting ? C.border : C.accent,
                color: '#fff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: submitting ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {submitting ? 'Submitting…' : 'Submit'}
            </button>
          </form>
        ) : (
          <p style={{ fontSize: '13px', color: C.muted, margin: 0 }}>
            <span style={{ color: C.accent, fontWeight: 600 }}>Sign in</span> to submit feedback.
          </p>
        )}
      </div>

      {/* Category tabs */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          marginBottom: '16px',
          borderBottom: `1px solid ${C.border}`,
          paddingBottom: '2px',
          flexWrap: 'wrap',
        }}
      >
        {CATEGORY_TABS.map((tab) => {
          const active = activeTab === tab.value;
          return (
            <button
              key={tab.label}
              onClick={() => handleTabChange(tab.value)}
              style={{
                padding: '6px 14px',
                borderRadius: '6px 6px 0 0',
                border: 'none',
                background: active ? C.surface : 'transparent',
                color: active ? C.text : C.muted,
                fontSize: '13px',
                fontWeight: active ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.1s',
                borderBottom: active ? `2px solid ${C.accent}` : '2px solid transparent',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Results count */}
      <div style={{ marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', color: C.muted }}>
          <span style={{ fontWeight: 600, color: C.text }}>{total}</span> item
          {total !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Feedback list */}
      {error ? (
        <div
          style={{
            padding: '32px',
            textAlign: 'center',
            color: C.red,
            fontSize: '13px',
            background: C.surface,
            borderRadius: '12px',
            border: `1px solid ${C.border}`,
          }}
        >
          {error}
        </div>
      ) : loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              style={{
                height: '80px',
                borderRadius: '10px',
                background: C.surface,
                border: `1px solid ${C.border}`,
                opacity: 0.5,
              }}
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div
          style={{
            padding: '48px',
            textAlign: 'center',
            color: C.dim,
            fontSize: '13px',
            background: C.surface,
            borderRadius: '12px',
            border: `1px solid ${C.border}`,
          }}
        >
          No feedback yet. Be the first to share!
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {items.map((item) => {
            const catColor = CATEGORY_COLORS[item.category] ?? C.accent;
            const catLabel = CATEGORY_LABELS[item.category] ?? item.category;
            return (
              <div
                key={item.id}
                style={{
                  background: C.surface,
                  border: `1px solid ${C.border}`,
                  borderRadius: '10px',
                  padding: '16px',
                  display: 'flex',
                  gap: '14px',
                  alignItems: 'flex-start',
                }}
              >
                {/* Upvote button */}
                <button
                  onClick={() => upvote(item.id)}
                  title="Upvote"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '2px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: `1px solid ${C.border}`,
                    background: C.bg,
                    color: C.muted,
                    cursor: 'pointer',
                    flexShrink: 0,
                    minWidth: '48px',
                    transition: 'all 0.15s',
                  }}
                >
                  <span style={{ fontSize: '12px' }}>▲</span>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
                    {item.upvotes}
                  </span>
                </button>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}
                  >
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: `${catColor}18`,
                        color: catColor,
                        fontWeight: 600,
                        border: `1px solid ${catColor}30`,
                      }}
                    >
                      {catLabel}
                    </span>
                    {item.status !== 'open' && (
                      <span
                        style={{
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: C.accentDim,
                          color: C.accent,
                          fontWeight: 500,
                        }}
                      >
                        {item.status}
                      </span>
                    )}
                    {item.created_at && (
                      <span style={{ fontSize: '11px', color: C.dim, marginLeft: 'auto' }}>
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <p
                    style={{
                      fontSize: '13px',
                      color: C.text,
                      margin: 0,
                      lineHeight: 1.55,
                      wordBreak: 'break-word',
                    }}
                  >
                    {item.body}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '8px',
            marginTop: '24px',
          }}
        >
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            style={{
              padding: '7px 16px',
              borderRadius: '8px',
              border: `1px solid ${C.border}`,
              background: C.surface,
              color: page === 1 ? C.dim : C.muted,
              cursor: page === 1 ? 'not-allowed' : 'pointer',
              fontSize: '13px',
            }}
          >
            Previous
          </button>
          <span style={{ fontSize: '13px', color: C.muted }}>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            style={{
              padding: '7px 16px',
              borderRadius: '8px',
              border: `1px solid ${C.border}`,
              background: C.surface,
              color: page === totalPages ? C.dim : C.muted,
              cursor: page === totalPages ? 'not-allowed' : 'pointer',
              fontSize: '13px',
            }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
