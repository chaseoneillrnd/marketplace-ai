import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CATEGORIES, type SkillSummary } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';
import { useSkillBrowse } from '../hooks/useSkills';
import { SkillCard } from '../components/SkillCard';
import { SkeletonCard } from '../components/SkeletonCard';
import { ErrorState } from '../components/ErrorState';

export function HomeView() {
  const C = useT();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [query, setQuery] = useState('');

  const { data: featured, loading: featuredLoading, error: featuredError, refetch: refetchFeatured } = useSkillBrowse({
    featured: true,
    per_page: 8,
  });

  const { data: suggested, loading: suggestedLoading } = useSkillBrowse({
    per_page: 4,
    ...(user?.division ? { divisions: [user.division] } : {}),
  });

  const handleSearch = () => {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '40px 24px' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <div
          style={{
            display: 'inline-flex',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: '99px',
            background: C.accentDim,
            border: `1px solid ${C.accent}33`,
            fontSize: '11px',
            color: C.accent,
            marginBottom: '16px',
            fontWeight: 500,
          }}
        >
          Internal Skills Registry
        </div>
        <h1 style={{ fontSize: '40px', fontWeight: 800, margin: '0 0 12px', lineHeight: 1.2 }}>
          <span style={{ color: C.text }}>Your organization&apos;s</span>
          <br />
          <span
            style={{
              background: `linear-gradient(135deg,${C.accent},${C.purple})`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              display: 'inline-block',
            }}
          >
            shared intelligence
          </span>
        </h1>
        <p style={{ fontSize: '15px', color: C.muted, maxWidth: '480px', margin: '0 auto 28px', lineHeight: '1.6' }}>
          Discover, install, and share Claude skills across every team and role.
        </p>
        <div style={{ maxWidth: '560px', margin: '0 auto', position: 'relative' }}>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="What do you need help with today?"
            style={{
              width: '100%',
              padding: '14px 120px 14px 18px',
              borderRadius: '12px',
              background: C.surface,
              border: `1px solid ${C.borderHi}`,
              fontSize: '15px',
              color: C.text,
              outline: 'none',
              boxShadow: C.mode === 'dark' ? '0 4px 24px rgba(0,0,0,0.3)' : '0 2px 12px rgba(0,0,0,0.08)',
            }}
          />
          <button
            onClick={handleSearch}
            style={{
              position: 'absolute',
              right: '6px',
              top: '50%',
              transform: 'translateY(-50%)',
              padding: '7px 16px',
              border: 'none',
              borderRadius: '8px',
              background: C.accent,
              color: '#fff',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
            }}
          >
            Search
          </button>
        </div>
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '16px', flexWrap: 'wrap' }}>
          {CATEGORIES.filter((c: typeof CATEGORIES[number]) => c !== 'All').map((cat: typeof CATEGORIES[number]) => (
            <button
              key={cat}
              onClick={() => navigate(`/filtered?category=${cat}`)}
              style={{
                background: C.surface,
                border: `1px solid ${C.border}`,
                color: C.muted,
                padding: '5px 14px',
                borderRadius: '99px',
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Suggested for You */}
      {user && (
        <section style={{ marginBottom: '40px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: C.text }}>Suggested for You</h2>
            <span style={{ fontSize: '11px', color: C.dim, fontFamily: "'JetBrains Mono',monospace" }}>
              {user.division}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: '14px' }}>
            {suggestedLoading
              ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
              : suggested?.items.map((s: SkillSummary) => (
                  <SkillCard key={s.id} skill={s} onClick={() => navigate(`/skills/${s.slug}`)} />
                ))}
          </div>
        </section>
      )}

      {/* Featured */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: C.text }}>Featured Skills</h2>
          <button
            onClick={() => navigate('/browse')}
            style={{ background: 'none', border: 'none', color: C.accent, cursor: 'pointer', fontSize: '13px' }}
          >
            View all &rarr;
          </button>
        </div>
        {featuredError ? (
          <ErrorState onRetry={refetchFeatured} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: '14px' }}>
            {featuredLoading
              ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
              : featured?.items.map((s: SkillSummary) => (
                  <SkillCard key={s.id} skill={s} onClick={() => navigate(`/skills/${s.slug}`)} />
                ))}
          </div>
        )}
      </section>
    </div>
  );
}
