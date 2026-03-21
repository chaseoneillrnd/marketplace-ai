import { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DIVISIONS, type SkillSummary } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { useSkillBrowse } from '../hooks/useSkills';
import { SkillCard } from '../components/SkillCard';
import { SkeletonCard } from '../components/SkeletonCard';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { DivisionFilterBar } from '../components/DivisionChip';

export function SearchView() {
  const C = useT();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const [selectedDivs, setSelectedDivs] = useState<string[]>([]);

  const { data, loading, error, refetch } = useSkillBrowse({
    q: query || undefined,
    divisions: selectedDivs.length > 0 ? selectedDivs : undefined,
  });

  const toggleDiv = useCallback((d: string) => {
    setSelectedDivs((s) => (s.includes(d) ? s.filter((x) => x !== d) : [...s, d]));
  }, []);

  const clearDivs = useCallback(() => setSelectedDivs([]), []);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
        <button
          onClick={() => navigate('/')}
          style={{ background: 'none', border: 'none', color: C.muted, cursor: 'pointer', fontSize: '20px' }}
        >
          &larr;
        </button>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 2px', color: C.text }}>
            {query ? (
              <>
                Results for <span style={{ color: C.accent }}>&quot;{query}&quot;</span>
              </>
            ) : (
              'All Skills'
            )}
          </h1>
          <span style={{ fontSize: '11px', color: C.muted }}>
            {data ? `${data.total} skills` : 'Searching...'}
          </span>
        </div>
      </div>

      <div style={{ marginBottom: '18px' }}>
        <DivisionFilterBar selected={selectedDivs} onToggle={toggleDiv} onClear={clearDivs} divisions={DIVISIONS} />
      </div>

      {error ? (
        <ErrorState onRetry={refetch} />
      ) : loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: '14px' }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : data && data.items.length === 0 ? (
        <EmptyState message={`No skills found for "${query}"`} onClear={() => navigate('/')} />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: '14px' }}>
          {data?.items.map((s: SkillSummary) => (
            <SkillCard key={s.id} skill={s} onClick={() => navigate(`/skills/${s.slug}`)} />
          ))}
        </div>
      )}
    </div>
  );
}
