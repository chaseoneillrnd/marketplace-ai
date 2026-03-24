import { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CATEGORIES, DIVISIONS, SORT_OPTIONS, INSTALL_LABELS, type SortOption, type SkillSummary } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';
import { useSkillBrowse } from '../hooks/useSkills';
import { SkillCard } from '../components/SkillCard';
import { SkeletonCard } from '../components/SkeletonCard';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { DivisionChip } from '../components/DivisionChip';
import { INSTALL_COLORS } from '../lib/theme';
import { DIVISION_COLORS } from '@skillhub/shared-types';

export function FilteredView() {
  const C = useT();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const initialCat = searchParams.get('category') ?? 'All';

  const [cat, setCat] = useState(initialCat);
  const [sort, setSort] = useState<SortOption>('trending');
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [savedOnly, setSavedOnly] = useState(false);
  const [installFilter, setInstallFilter] = useState('All');
  const [selectedDivs, setSelectedDivs] = useState<string[]>([]);
  const [page, setPage] = useState(1);

  const { data, loading, error, refetch } = useSkillBrowse({
    category: cat !== 'All' ? cat : undefined,
    divisions: selectedDivs.length > 0 ? selectedDivs : undefined,
    sort,
    install_method: installFilter !== 'All' ? installFilter : undefined,
    verified: verifiedOnly || undefined,
    favorited: savedOnly || undefined,
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

  const pill = (label: string, active: boolean, onClick: () => void, color = C.accent) => (
    <button
      key={label}
      onClick={onClick}
      style={{
        padding: '5px 12px',
        borderRadius: '6px',
        fontSize: '12px',
        cursor: 'pointer',
        transition: 'all 0.1s',
        border: `1px solid ${active ? color : C.border}`,
        background: active ? `${color}14` : 'transparent',
        color: active ? color : C.muted,
      }}
    >
      {label}
    </button>
  );

  const section = (title: string, content: React.ReactNode) => (
    <div
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '10px',
      }}
    >
      <h3
        style={{
          fontSize: '11px',
          fontWeight: 600,
          color: C.dim,
          textTransform: 'uppercase',
          letterSpacing: '1px',
          margin: '0 0 10px',
        }}
      >
        {title}
      </h3>
      {content}
    </div>
  );

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 24px', display: 'flex', gap: '24px' }}>
      {/* Sidebar */}
      <div style={{ width: '230px', flexShrink: 0 }}>
        <div style={{ position: 'sticky', top: '80px' }}>
          {section(
            'Category',
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {CATEGORIES.map((c: typeof CATEGORIES[number]) =>
                pill(c, cat === c, () => {
                  setCat(c);
                  setPage(1);
                }),
              )}
            </div>,
          )}

          {/* Division multi-select */}
          <div
            style={{
              background: C.surface,
              border: `1px solid ${C.border}`,
              borderRadius: '12px',
              padding: '16px',
              marginBottom: '10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: C.dim,
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  margin: 0,
                }}
              >
                Division{' '}
                {selectedDivs.length > 0 && (
                  <span
                    style={{
                      background: C.accentDim,
                      color: C.accent,
                      borderRadius: '99px',
                      padding: '1px 7px',
                      fontSize: '10px',
                    }}
                  >
                    {selectedDivs.length}
                  </span>
                )}
              </h3>
              {selectedDivs.length > 0 && (
                <button
                  onClick={clearDivs}
                  style={{
                    fontSize: '10px',
                    color: C.dim,
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  Clear
                </button>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {DIVISIONS.map((d: typeof DIVISIONS[number]) => {
                const active = selectedDivs.includes(d);
                const color = DIVISION_COLORS[d] ?? C.accent;
                return (
                  <button
                    key={d}
                    onClick={() => toggleDiv(d)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '5px 8px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.1s',
                      background: active ? `${color}10` : 'transparent',
                      border: `1px solid ${active ? color + '33' : 'transparent'}`,
                    }}
                  >
                    <div
                      style={{
                        width: '14px',
                        height: '14px',
                        borderRadius: '3px',
                        flexShrink: 0,
                        border: `2px solid ${active ? color : C.border}`,
                        background: active ? color : 'transparent',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '9px',
                        color: '#fff',
                      }}
                    >
                      {active ? '\u2713' : ''}
                    </div>
                    <span style={{ fontSize: '12px', color: active ? color : C.muted, fontWeight: active ? 600 : 400 }}>
                      {d}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {section(
            'Sort By',
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {SORT_OPTIONS.map((s: typeof SORT_OPTIONS[number]) =>
                pill(s.label, sort === s.value, () => {
                  setSort(s.value);
                  setPage(1);
                }),
              )}
            </div>,
          )}

          {section(
            'Install Method',
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {['All', 'claude-code', 'mcp', 'manual'].map((m) =>
                pill(
                  m === 'All' ? 'All' : (INSTALL_LABELS[m] ?? m),
                  installFilter === m,
                  () => {
                    setInstallFilter(m);
                    setPage(1);
                  },
                  INSTALL_COLORS[m] ?? C.accent,
                ),
              )}
            </div>,
          )}

          {section(
            'Quality',
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={verifiedOnly}
                  onChange={(e) => {
                    setVerifiedOnly(e.target.checked);
                    setPage(1);
                  }}
                  style={{ accentColor: C.accent }}
                />
                <span style={{ fontSize: '12px', color: C.muted }}>Verified only</span>
              </label>
              {user && (
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={savedOnly}
                    onChange={(e) => {
                      setSavedOnly(e.target.checked);
                      setPage(1);
                    }}
                    style={{ accentColor: C.accent }}
                  />
                  <span style={{ fontSize: '12px', color: C.muted }}>Saved only</span>
                </label>
              )}
            </div>,
          )}
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <span style={{ fontSize: '13px', color: C.muted }}>
            <span style={{ fontWeight: 600, color: C.text }}>{data?.total ?? '...'}</span> skills
          </span>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {cat !== 'All' && (
              <span
                style={{
                  fontSize: '11px',
                  padding: '3px 10px',
                  borderRadius: '99px',
                  background: C.accentDim,
                  color: C.accent,
                  border: `1px solid ${C.accent}30`,
                }}
              >
                {cat}
              </span>
            )}
            {selectedDivs.map((d) => (
              <DivisionChip key={d} division={d} active small />
            ))}
            {verifiedOnly && (
              <span
                style={{
                  fontSize: '11px',
                  padding: '3px 10px',
                  borderRadius: '99px',
                  background: C.amberDim,
                  color: C.amber,
                  border: `1px solid ${C.amber}30`,
                }}
              >
                Verified
              </span>
            )}
            {savedOnly && (
              <span
                style={{
                  fontSize: '11px',
                  padding: '3px 10px',
                  borderRadius: '99px',
                  background: C.accentDim,
                  color: C.accent,
                  border: `1px solid ${C.accent}30`,
                }}
              >
                Saved
              </span>
            )}
          </div>
        </div>

        {error ? (
          <ErrorState onRetry={refetch} />
        ) : loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))', gap: '14px' }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : data && data.items.length === 0 ? (
          <EmptyState
            onClear={() => {
              setCat('All');
              clearDivs();
              setVerifiedOnly(false);
              setSavedOnly(false);
              setInstallFilter('All');
            }}
          />
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))', gap: '14px' }}>
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
    </div>
  );
}
