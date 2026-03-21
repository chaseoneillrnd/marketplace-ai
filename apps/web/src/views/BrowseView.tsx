import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CATEGORIES, DIVISIONS, type SkillSummary } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { useSkillBrowse } from '../hooks/useSkills';
import { SkillCard } from '../components/SkillCard';
import { SkeletonCard } from '../components/SkeletonCard';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { DivisionFilterBar } from '../components/DivisionChip';

export function BrowseView() {
  const C = useT();
  const navigate = useNavigate();
  const [activeCat, setActiveCat] = useState('All');
  const [selectedDivs, setSelectedDivs] = useState<string[]>([]);
  const [page, setPage] = useState(1);

  const { data, loading, error, refetch } = useSkillBrowse({
    category: activeCat !== 'All' ? activeCat : undefined,
    divisions: selectedDivs.length > 0 ? selectedDivs : undefined,
    page,
    per_page: 20,
  });

  const toggleDiv = useCallback((d: string) => {
    setSelectedDivs((s) => (s.includes(d) ? s.filter((x) => x !== d) : [...s, d]));
    setPage(1);
  }, []);

  const clearDivs = useCallback(() => {
    setSelectedDivs([]);
    setPage(1);
  }, []);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, margin: '0 0 4px', color: C.text }}>All Skills</h1>
          <span style={{ fontSize: '12px', color: C.muted }}>
            {data ? `${data.total} skills` : 'Loading...'}
          </span>
        </div>
        <button
          onClick={() => navigate('/filtered')}
          style={{
            padding: '5px 12px',
            fontSize: '12px',
            borderRadius: '8px',
            border: `1px solid ${C.border}`,
            background: C.surface,
            color: C.muted,
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Advanced Filters
        </button>
      </div>

      {/* Category pills */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '10px', flexWrap: 'wrap' }}>
        {CATEGORIES.map((cat: typeof CATEGORIES[number]) => {
          const active = activeCat === cat;
          return (
            <button
              key={cat}
              onClick={() => {
                setActiveCat(cat);
                setPage(1);
              }}
              style={{
                padding: '5px 14px',
                borderRadius: '99px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: active ? 600 : 400,
                transition: 'all 0.15s',
                border: `1px solid ${active ? C.accent : C.border}`,
                background: active ? C.accentDim : C.surface,
                color: active ? C.accent : C.muted,
              }}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Division filter */}
      <div style={{ marginBottom: '20px' }}>
        <DivisionFilterBar selected={selectedDivs} onToggle={toggleDiv} onClear={clearDivs} divisions={DIVISIONS} />
      </div>

      {/* Skills grid */}
      {error ? (
        <ErrorState onRetry={refetch} />
      ) : loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: '14px' }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : data && data.items.length === 0 ? (
        <EmptyState
          onClear={() => {
            setActiveCat('All');
            clearDivs();
          }}
        />
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: '14px' }}>
            {data?.items.map((s: SkillSummary) => (
              <SkillCard key={s.id} skill={s} onClick={() => navigate(`/skills/${s.slug}`)} />
            ))}
          </div>
          {data && data.has_more && (
            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <button
                onClick={() => setPage((p) => p + 1)}
                style={{
                  padding: '10px 28px',
                  borderRadius: '8px',
                  border: `1px solid ${C.border}`,
                  background: C.surface,
                  color: C.muted,
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                }}
              >
                Load more
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
