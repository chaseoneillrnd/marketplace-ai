import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { INSTALL_LABELS } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';
import { useSkillDetail } from '../hooks/useSkills';
import { useFlag } from '../hooks/useFlag';
import { useReviews } from '../hooks/useReviews';
import { DivisionChip } from '../components/DivisionChip';
import { SkeletonCard } from '../components/SkeletonCard';
import { ErrorState } from '../components/ErrorState';
import { INSTALL_COLORS } from '../lib/theme';
import { api } from '../lib/api';

export function SkillDetailView() {
  const C = useT();
  const navigate = useNavigate();
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const mcpInstallEnabled = useFlag('mcp_install_enabled');

  const { data: skill, loading, error, refetch } = useSkillDetail(slug);
  const [tab, setTab] = useState('overview');
  const [installed, setInstalled] = useState(false);
  const [favorited, setFavorited] = useState(false);
  const [reqAccess, setReqAccess] = useState(false);

  useEffect(() => {
    if (skill) {
      setInstalled(!!skill.user_has_installed);
      setFavorited(!!skill.user_has_favorited);
    }
  }, [skill]);
  const [reqAccessError, setReqAccessError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  if (loading) {
    return (
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 24px' }}>
        <SkeletonCard />
      </div>
    );
  }

  if (error || !skill) {
    return (
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 24px' }}>
        <ErrorState message={error ?? 'Skill not found'} onRetry={refetch} />
      </div>
    );
  }

  const userDiv = user?.division ?? null;
  const hasAccess = !userDiv || skill.divisions.includes(userDiv);
  const accent = skill.author_type === 'official' ? C.accent : C.green;

  const handleInstall = async () => {
    if (!hasAccess || installed) return;
    setActionError(null);
    try {
      await api.post(`/api/v1/skills/${skill.slug}/install`, {
        method: skill.install_method,
        version: skill.current_version,
      });
      setInstalled(true);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Install failed');
    }
  };

  const handleFavorite = async () => {
    setActionError(null);
    try {
      if (favorited) {
        await api.delete(`/api/v1/skills/${skill.slug}/favorite`);
        setFavorited(false);
      } else {
        await api.post(`/api/v1/skills/${skill.slug}/favorite`);
        setFavorited(true);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action failed');
    }
  };

  const handleFork = async () => {
    setActionError(null);
    try {
      const result = await api.post<{ forked_skill_slug: string }>(`/api/v1/skills/${skill.slug}/fork`);
      navigate(`/skills/${result.forked_skill_slug}`);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Fork failed');
    }
  };

  const handleFollow = async () => {
    setActionError(null);
    try {
      await api.post(`/api/v1/skills/${skill.slug}/follow`);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Follow failed');
    }
  };

  const tabs = ['overview', 'how-to-use', 'install', 'reviews'] as const;
  const tabLabels: Record<string, string> = {
    overview: 'Overview',
    'how-to-use': 'How to Use',
    install: 'Install',
    reviews: 'Reviews',
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 24px' }}>
      <button
        onClick={() => navigate(-1)}
        style={{
          background: 'none',
          border: 'none',
          color: C.muted,
          cursor: 'pointer',
          fontSize: '13px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        &larr; Back
      </button>

      {/* Access warning */}
      {user && !hasAccess && (
        <div
          style={{
            padding: '16px 20px',
            background: C.amberDim,
            border: `1px solid ${C.amber}44`,
            borderRadius: '12px',
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '16px',
          }}
        >
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: C.amber, marginBottom: '4px' }}>
              Access restricted for your division
            </div>
            <div style={{ fontSize: '12px', color: C.amber, opacity: 0.8, lineHeight: '1.5' }}>
              Approved for: {skill.divisions.join(', ')} &middot; Your division: {userDiv}
            </div>
          </div>
          <button
            onClick={async () => {
              if (reqAccess) return;
              try {
                setReqAccessError(null);
                await api.post(`/api/v1/skills/${skill.slug}/access-request`, {
                  reason: `${userDiv} needs access to this skill`,
                });
                setReqAccess(true);
              } catch (err) {
                setReqAccessError(err instanceof Error ? err.message : 'Failed to request access');
              }
            }}
            disabled={reqAccess}
            style={{
              padding: '5px 12px',
              borderRadius: '8px',
              border: `1px solid ${C.border}`,
              background: reqAccess ? `${C.green}18` : C.surface,
              color: reqAccess ? C.green : C.muted,
              cursor: reqAccess ? 'default' : 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            {reqAccess ? '\u2713 Requested' : 'Request Access'}
          </button>
          {reqAccessError && (
            <div style={{ fontSize: '11px', color: C.red, marginTop: '4px' }}>{reqAccessError}</div>
          )}
        </div>
      )}

      {/* Header card */}
      <div
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '14px',
          overflow: 'hidden',
          marginBottom: '2px',
          boxShadow: C.mode === 'light' ? '0 2px 12px rgba(0,0,0,0.06)' : 'none',
        }}
      >
        <div style={{ height: '4px', background: `linear-gradient(90deg,${accent},${accent}44,transparent)` }} />
        <div style={{ padding: '24px 28px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: '20px',
              marginBottom: '18px',
            }}
          >
            <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '10px',
                  background: `${accent}18`,
                  border: `1px solid ${accent}30`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                  fontWeight: 800,
                  color: accent,
                  fontFamily: "'JetBrains Mono',monospace",
                  flexShrink: 0,
                }}
              >
                {skill.name[0]}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <h1 style={{ fontSize: '22px', fontWeight: 700, margin: 0, color: C.text }}>{skill.name}</h1>
                  {skill.verified && (
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '2px 7px',
                        borderRadius: '4px',
                        background: C.amberDim,
                        color: C.amber,
                        fontWeight: 600,
                      }}
                    >
                      Verified
                    </span>
                  )}
                  {skill.featured && (
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '2px 7px',
                        borderRadius: '4px',
                        background: C.accentDim,
                        color: C.accent,
                        fontWeight: 600,
                      }}
                    >
                      Featured
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: C.muted }}>
                  <span>
                    by <span style={{ color: C.text }}>{skill.author ?? 'Unknown'}</span>
                  </span>
                  <span
                    style={{
                      fontSize: '10px',
                      padding: '2px 9px',
                      borderRadius: '99px',
                      background: `${accent}18`,
                      color: accent,
                      border: `1px solid ${accent}28`,
                      fontWeight: 500,
                    }}
                  >
                    {skill.author_type}
                  </span>
                  <span style={{ fontFamily: "'JetBrains Mono',monospace", color: C.dim }}>v{skill.current_version}</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
                  {skill.divisions.map((d) => (
                    <DivisionChip key={d} division={d} small />
                  ))}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px', flexShrink: 0, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <button
                onClick={handleFavorite}
                style={{
                  padding: '5px 12px',
                  fontSize: '12px',
                  borderRadius: '8px',
                  border: `1px solid ${C.border}`,
                  background: C.surface,
                  color: favorited ? C.amber : C.muted,
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                {favorited ? '\u2605 Saved' : '\u2606 Save'}
              </button>
              {user ? (
                <button
                  onClick={handleInstall}
                  disabled={!hasAccess && !reqAccess}
                  style={{
                    padding: '5px 12px',
                    fontSize: '12px',
                    borderRadius: '8px',
                    border: 'none',
                    background: C.accent,
                    color: '#fff',
                    cursor: !hasAccess ? 'not-allowed' : 'pointer',
                    fontWeight: 600,
                    opacity: !hasAccess ? 0.5 : 1,
                  }}
                >
                  {installed ? '\u2713 Installed' : hasAccess ? 'Install' : 'Restricted'}
                </button>
              ) : (
                <button
                  onClick={() => navigate('/')}
                  style={{
                    padding: '5px 12px',
                    fontSize: '12px',
                    borderRadius: '8px',
                    border: 'none',
                    background: C.accent,
                    color: '#fff',
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  Sign in to Install
                </button>
              )}
            </div>
          </div>

          {/* Stats bar */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4,1fr)',
              gap: '1px',
              background: C.border,
              borderRadius: '10px',
              overflow: 'hidden',
            }}
          >
            {[
              { icon: '\u2193', value: skill.install_count, label: 'Installs' },
              { icon: '\u2605', value: Number(skill.avg_rating).toFixed(1), label: 'Rating' },
              { icon: '\u2197', value: skill.fork_count, label: 'Forks' },
              { icon: '\u2661', value: skill.favorite_count, label: 'Favorites' },
            ].map((m) => (
              <div key={m.label} style={{ background: C.surface, padding: '14px', textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 700, color: C.text }}>
                  {typeof m.value === 'number' ? m.value.toLocaleString() : m.value}
                </div>
                <div style={{ fontSize: '10px', color: C.muted, marginTop: '2px' }}>
                  {m.icon} {m.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div style={{ borderTop: `1px solid ${C.border}`, padding: '0 16px', display: 'flex', overflowX: 'auto' }}>
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: '8px 18px',
                fontSize: '13px',
                fontWeight: tab === t ? 600 : 400,
                cursor: 'pointer',
                border: 'none',
                background: 'none',
                color: tab === t ? C.text : C.muted,
                borderBottom: `2px solid ${tab === t ? C.accent : 'transparent'}`,
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              {tabLabels[t]}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div
        style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: '14px',
          padding: '28px',
          marginTop: '2px',
          boxShadow: C.mode === 'light' ? '0 2px 12px rgba(0,0,0,0.05)' : 'none',
        }}
      >
        {tab === 'overview' && (
          <div>
            <p style={{ fontSize: '14px', color: C.muted, lineHeight: '1.7', margin: '0 0 22px' }}>{skill.short_desc}.</p>

            {skill.trigger_phrases.length > 0 && (
              <>
                <h3
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: C.dim,
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    margin: '0 0 8px',
                  }}
                >
                  Trigger Phrases
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '18px' }}>
                  {skill.trigger_phrases.map((t) => (
                    <span
                      key={t.id}
                      style={{
                        padding: '5px 12px',
                        borderRadius: '6px',
                        background: C.accentDim,
                        color: C.accent,
                        fontFamily: "'JetBrains Mono',monospace",
                        fontSize: '12px',
                        border: `1px solid ${C.accent}22`,
                      }}
                    >
                      &quot;{t.phrase}&quot;
                    </span>
                  ))}
                </div>
              </>
            )}

            <h3
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: C.dim,
                textTransform: 'uppercase',
                letterSpacing: '1px',
                margin: '0 0 8px',
              }}
            >
              Authorized Divisions
            </h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {skill.divisions.map((d) => (
                <DivisionChip key={d} division={d} />
              ))}
            </div>
          </div>
        )}

        {tab === 'how-to-use' && skill.current_version_content && (
          <div>
            <h3
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: C.dim,
                textTransform: 'uppercase',
                letterSpacing: '1px',
                margin: '0 0 8px',
              }}
            >
              Skill Content
            </h3>
            <div
              style={{
                padding: '16px',
                background: C.bg,
                borderRadius: '8px',
                border: `1px solid ${C.border}`,
              }}
            >
              <pre
                style={{
                  margin: 0,
                  fontSize: '12px',
                  color: C.muted,
                  fontFamily: "'JetBrains Mono',monospace",
                  whiteSpace: 'pre-wrap',
                  lineHeight: '1.7',
                }}
              >
                {skill.current_version_content.content}
              </pre>
            </div>
          </div>
        )}

        {tab === 'install' && (
          <div>
            {!hasAccess && user && (
              <div
                style={{
                  padding: '12px 16px',
                  background: C.redDim,
                  border: `1px solid ${C.red}30`,
                  borderRadius: '8px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ fontSize: '13px', color: C.red, fontWeight: 600, marginBottom: '4px' }}>
                  Installation restricted
                </div>
                <div style={{ fontSize: '12px', color: C.red, opacity: 0.8, lineHeight: '1.5' }}>
                  Your division ({userDiv}) is not authorized. Request access above.
                </div>
              </div>
            )}
            {[
              {
                method: 'claude-code',
                label: 'Claude Code CLI',
                cmd: `claude skill install ${skill.slug}`,
                desc: 'Recommended for developers.',
              },
              ...(mcpInstallEnabled ? [{
                method: 'mcp',
                label: 'MCP Server',
                cmd: `# SkillHub MCP -> install_skill("${skill.slug}")`,
                desc: 'For teams using the SkillHub MCP server.',
              }] : []),
              {
                method: 'manual',
                label: 'Manual Install',
                cmd: `# Copy SKILL.md to:\n/mnt/skills/user/${skill.slug}/SKILL.md`,
                desc: 'Works in all Claude environments.',
              },
            ].map((m) => (
              <div
                key={m.method}
                style={{
                  marginBottom: '14px',
                  padding: '16px',
                  background: C.bg,
                  borderRadius: '10px',
                  border: `1px solid ${m.method === skill.install_method ? (INSTALL_COLORS[m.method] ?? C.accent) + '44' : C.border}`,
                  opacity: !hasAccess && user ? 0.5 : 1,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 600, fontSize: '14px', color: C.text }}>{m.label}</span>
                  {m.method === skill.install_method && (
                    <span
                      style={{
                        fontSize: '10px',
                        padding: '2px 9px',
                        borderRadius: '99px',
                        background: `${INSTALL_COLORS[m.method] ?? C.accent}18`,
                        color: INSTALL_COLORS[m.method] ?? C.accent,
                        fontWeight: 500,
                      }}
                    >
                      Recommended
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '12px', color: C.muted, margin: '0 0 10px' }}>{m.desc}</p>
                <div style={{ background: C.codeBg, borderRadius: '6px', padding: '10px 14px' }}>
                  <pre
                    style={{
                      margin: 0,
                      fontSize: '11px',
                      color: C.mode === 'dark' ? '#5af2b0' : '#0a5c38',
                      fontFamily: "'JetBrains Mono',monospace",
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {m.cmd}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === 'reviews' && <ReviewsSection slug={skill.slug} user={user} C={C} />}
      </div>
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffSec = Math.floor((now - then) / 1000);
  if (diffSec < 60) return 'just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;
  const diffMonth = Math.floor(diffDay / 30);
  if (diffMonth < 12) return `${diffMonth}mo ago`;
  return `${Math.floor(diffMonth / 12)}y ago`;
}

function StarDisplay({ rating, color }: { rating: number; color: string }) {
  return (
    <span style={{ color, fontSize: '14px', letterSpacing: '1px' }} data-testid="star-display">
      {Array.from({ length: 5 }, (_, i) => (i < rating ? '\u2605' : '\u2606')).join('')}
    </span>
  );
}

function StarPicker({
  value,
  onChange,
  color,
}: {
  value: number;
  onChange: (v: number) => void;
  color: string;
}) {
  return (
    <div style={{ display: 'flex', gap: '4px' }} data-testid="star-picker">
      {Array.from({ length: 5 }, (_, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onChange(i + 1)}
          aria-label={`${i + 1} star${i === 0 ? '' : 's'}`}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '20px',
            color: i < value ? color : '#666',
            padding: '0 2px',
          }}
        >
          {i < value ? '\u2605' : '\u2606'}
        </button>
      ))}
    </div>
  );
}

interface ReviewsSectionProps {
  slug: string;
  user: { user_id?: string; name?: string } | null;
  C: ReturnType<typeof useT>;
}

function ReviewsSection({ slug, user, C }: ReviewsSectionProps) {
  const { data: reviews, loading, error, refetch } = useReviews(slug);
  const [rating, setRating] = useState(0);
  const [body, setBody] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0 || !body.trim()) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api.post(`/api/v1/skills/${slug}/reviews`, { rating, body: body.trim() });
      setRating(0);
      setBody('');
      refetch();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {user && (
        <form onSubmit={handleSubmit} style={{ marginBottom: '24px' }}>
          <h3
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: C.dim,
              textTransform: 'uppercase',
              letterSpacing: '1px',
              margin: '0 0 10px',
            }}
          >
            Write a Review
          </h3>
          <div style={{ marginBottom: '10px' }}>
            <StarPicker value={rating} onChange={setRating} color={C.amber} />
          </div>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Share your experience with this skill..."
            rows={3}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: '8px',
              border: `1px solid ${C.border}`,
              background: C.bg,
              color: C.text,
              fontSize: '13px',
              fontFamily: 'inherit',
              resize: 'vertical',
              boxSizing: 'border-box',
            }}
          />
          {submitError && (
            <div style={{ fontSize: '12px', color: C.red, marginTop: '6px' }}>{submitError}</div>
          )}
          <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="submit"
              disabled={submitting || rating === 0 || !body.trim()}
              style={{
                padding: '6px 16px',
                borderRadius: '8px',
                border: 'none',
                background: rating > 0 && body.trim() ? C.accent : C.border,
                color: rating > 0 && body.trim() ? '#fff' : C.muted,
                cursor: rating > 0 && body.trim() ? 'pointer' : 'not-allowed',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              {submitting ? 'Submitting...' : 'Submit Review'}
            </button>
          </div>
        </form>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '20px 0', color: C.muted, fontSize: '13px' }}>
          Loading reviews...
        </div>
      )}

      {error && (
        <div style={{ textAlign: 'center', padding: '20px 0', color: C.red, fontSize: '13px' }}>
          Failed to load reviews
        </div>
      )}

      {reviews && reviews.items.length === 0 && (
        <div style={{ textAlign: 'center', padding: '30px 0', color: C.muted, fontSize: '13px' }}>
          No reviews yet. Be the first to review this skill.
        </div>
      )}

      {reviews && reviews.items.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {reviews.items.map((r) => (
            <div
              key={r.id}
              style={{
                padding: '14px 16px',
                background: C.bg,
                borderRadius: '10px',
                border: `1px solid ${C.border}`,
              }}
              data-testid="review-item"
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <StarDisplay rating={r.rating} color={C.amber} />
                  <span style={{ fontSize: '12px', fontWeight: 600, color: C.text }}>{r.user_id}</span>
                </div>
                <span style={{ fontSize: '11px', color: C.dim }}>{formatRelativeTime(r.created_at)}</span>
              </div>
              <p style={{ fontSize: '13px', color: C.muted, lineHeight: '1.6', margin: 0 }}>{r.body}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
