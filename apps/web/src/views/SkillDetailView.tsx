import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { INSTALL_LABELS } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';
import { useSkillDetail } from '../hooks/useSkills';
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

  const { data: skill, loading, error, refetch } = useSkillDetail(slug);
  const [tab, setTab] = useState('overview');
  const [installed, setInstalled] = useState(false);
  const [favorited, setFavorited] = useState(false);
  const [reqAccess, setReqAccess] = useState(false);

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
    try {
      await api.post(`/api/v1/skills/${skill.slug}/install`, {
        method: skill.install_method,
        version: skill.current_version,
      });
      setInstalled(true);
    } catch {
      // Silent fail — could show toast
    }
  };

  const handleFavorite = async () => {
    try {
      if (favorited) {
        await api.delete(`/api/v1/skills/${skill.slug}/favorite`);
        setFavorited(false);
      } else {
        await api.post(`/api/v1/skills/${skill.slug}/favorite`);
        setFavorited(true);
      }
    } catch {
      // Silent fail
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
            onClick={() => setReqAccess(!reqAccess)}
            style={{
              padding: '5px 12px',
              borderRadius: '8px',
              border: `1px solid ${C.border}`,
              background: C.surface,
              color: C.muted,
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            {reqAccess ? '\u2713 Requested' : 'Request Access'}
          </button>
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
                    by <span style={{ color: C.text }}>{skill.author}</span>
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
              {
                method: 'mcp',
                label: 'MCP Server',
                cmd: `# SkillHub MCP -> install_skill("${skill.slug}")`,
                desc: 'For teams using the SkillHub MCP server.',
              },
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

        {tab === 'reviews' && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: C.muted }}>
            <div style={{ fontSize: '14px' }}>
              {skill.review_count} reviews &middot; {Number(skill.avg_rating).toFixed(1)} avg rating
            </div>
            <div style={{ fontSize: '12px', marginTop: '8px', color: C.dim }}>
              Full reviews UI coming soon
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
