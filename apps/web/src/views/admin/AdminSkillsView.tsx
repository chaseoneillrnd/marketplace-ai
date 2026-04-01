import { useState, useEffect, useRef } from 'react';
import { useT } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';
import { useAdminSkills } from '../../hooks/useAdminSkills';
import { AdminConfirmDialog } from '../../components/admin/AdminConfirmDialog';
import { AdminLoadingSkeleton } from '../../components/admin/AdminLoadingSkeleton';
import type { SkillSummary } from '@skillhub/shared-types';

const PER_PAGE = 20;

function statusPill(
  status: string,
  featured: boolean,
  C: ReturnType<typeof useT>,
): React.ReactElement {
  if (status === 'deprecated') {
    return (
      <span
        style={{
          display: 'inline-block',
          padding: '3px 10px',
          borderRadius: '99px',
          fontSize: '11px',
          fontWeight: 600,
          background: C.amberDim,
          color: C.amber,
          fontFamily: 'Outfit, sans-serif',
        }}
      >
        deprecated
      </span>
    );
  }
  if (status === 'removed') {
    return (
      <span
        style={{
          display: 'inline-block',
          padding: '3px 10px',
          borderRadius: '99px',
          fontSize: '11px',
          fontWeight: 600,
          background: C.redDim,
          color: C.red,
          fontFamily: 'Outfit, sans-serif',
        }}
      >
        removed
      </span>
    );
  }
  // published (default)
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '3px 10px',
        borderRadius: '99px',
        fontSize: '11px',
        fontWeight: 600,
        background: featured ? C.accentDim : C.greenDim,
        color: featured ? C.accent : C.green,
        fontFamily: 'Outfit, sans-serif',
      }}
    >
      {featured ? 'featured' : 'published'}
    </span>
  );
}

interface DeprecateDialogState {
  skill: SkillSummary;
}

interface RemoveDialogState {
  skill: SkillSummary;
}

export function AdminSkillsView() {
  const C = useT();
  const { user } = useAuth();
  const isSecurityTeam = user?.is_security_team ?? false;

  const { skills, total, page, loading, error, featureSkill, deprecateSkill, removeSkill, setPage, setSearch } =
    useAdminSkills();

  const [searchInput, setSearchInput] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [deprecateTarget, setDeprecateTarget] = useState<DeprecateDialogState | null>(null);
  const [removeTarget, setRemoveTarget] = useState<RemoveDialogState | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setSearch(searchInput);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchInput, setSearch]);

  const totalPages = total > 0 ? Math.ceil(total / PER_PAGE) : 1;

  const handleFeatureToggle = async (skill: SkillSummary) => {
    await featureSkill(skill.slug, !skill.featured);
  };

  const handleDeprecateConfirm = async () => {
    if (!deprecateTarget) return;
    await deprecateSkill(deprecateTarget.skill.slug);
    setDeprecateTarget(null);
  };

  const handleRemoveConfirm = async () => {
    if (!removeTarget) return;
    await removeSkill(removeTarget.skill.slug);
    setRemoveTarget(null);
  };

  const inputStyle: React.CSSProperties = {
    background: C.inputBg,
    border: `1px solid ${C.border}`,
    borderRadius: '8px',
    padding: '8px 14px',
    color: C.text,
    fontSize: '13px',
    fontFamily: 'Outfit, sans-serif',
    outline: 'none',
    width: '280px',
  };

  const chipStyle = (disabled?: boolean): React.CSSProperties => ({
    padding: '5px 12px',
    borderRadius: '99px',
    border: `1px solid ${C.border}`,
    background: 'transparent',
    color: disabled ? C.dim : C.muted,
    fontSize: '12px',
    fontWeight: 500,
    fontFamily: 'Outfit, sans-serif',
    cursor: disabled ? 'default' : 'pointer',
    opacity: disabled ? 0.45 : 1,
    transition: 'all 0.15s',
  });

  const actionBtn = (variant: 'default' | 'amber' | 'red'): React.CSSProperties => {
    const map = {
      default: { bg: C.accentDim, color: C.accent, border: C.accent },
      amber: { bg: C.amberDim, color: C.amber, border: C.amber },
      red: { bg: C.redDim, color: C.red, border: C.red },
    };
    const v = map[variant];
    return {
      padding: '4px 10px',
      borderRadius: '6px',
      border: `1px solid ${v.border}`,
      background: v.bg,
      color: v.color,
      fontSize: '11px',
      fontWeight: 600,
      fontFamily: 'Outfit, sans-serif',
      cursor: 'pointer',
      transition: 'all 0.15s',
      whiteSpace: 'nowrap' as const,
    };
  };

  const thStyle: React.CSSProperties = {
    padding: '10px 14px',
    textAlign: 'left',
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.6px',
    color: C.dim,
    borderBottom: `1px solid ${C.border}`,
    whiteSpace: 'nowrap',
  };

  const tdStyle: React.CSSProperties = {
    padding: '12px 14px',
    fontSize: '13px',
    color: C.text,
    borderBottom: `1px solid ${C.border}`,
    verticalAlign: 'middle',
  };

  if (loading && skills.length === 0) {
    return <AdminLoadingSkeleton />;
  }

  return (
    <div data-testid="admin-skills-view">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: C.text }}>Skills</h1>
        <input
          style={inputStyle}
          placeholder="Search skills..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          data-testid="skills-search-input"
          aria-label="Search skills"
        />
      </div>

      {/* Error */}
      {error && (
        <p style={{ color: C.red, fontSize: '13px', marginBottom: '16px' }}>{error}</p>
      )}

      {/* Empty state */}
      {!loading && skills.length === 0 && (
        <p style={{ color: C.muted, fontSize: '13px' }}>No skills found.</p>
      )}

      {/* Table */}
      {skills.length > 0 && (
        <div
          style={{
            background: C.surface,
            border: `1px solid ${C.border}`,
            borderRadius: '12px',
            overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Category</th>
                <th style={thStyle}>Version</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Installs</th>
                <th style={thStyle}>Status</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {skills.map((skill) => (
                <tr key={skill.slug} data-testid={`skill-row-${skill.slug}`}>
                  {/* Name */}
                  <td style={tdStyle}>
                    <div style={{ fontWeight: 600, color: C.text, marginBottom: '2px' }}>{skill.name}</div>
                    <div style={{ fontSize: '11px', color: C.muted, fontFamily: 'JetBrains Mono, monospace' }}>
                      {skill.slug}
                    </div>
                  </td>

                  {/* Category */}
                  <td style={tdStyle}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        background: C.purpleDim,
                        color: C.purple,
                        fontSize: '11px',
                        fontWeight: 500,
                        fontFamily: 'Outfit, sans-serif',
                      }}
                    >
                      {skill.category}
                    </span>
                  </td>

                  {/* Version */}
                  <td style={{ ...tdStyle, fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', color: C.muted }}>
                    {skill.version}
                  </td>

                  {/* Installs */}
                  <td style={{ ...tdStyle, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {skill.install_count.toLocaleString()}
                  </td>

                  {/* Status */}
                  <td style={tdStyle}>
                    {statusPill((skill as SkillSummary & { status?: string }).status ?? 'published', skill.featured, C)}
                  </td>

                  {/* Actions */}
                  <td style={{ ...tdStyle, textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end', alignItems: 'center' }}>
                      {/* Feature / Unfeature toggle */}
                      <button
                        style={actionBtn('default')}
                        onClick={() => handleFeatureToggle(skill)}
                        data-testid={`feature-btn-${skill.slug}`}
                        aria-label={skill.featured ? `Unfeature ${skill.name}` : `Feature ${skill.name}`}
                      >
                        {skill.featured ? 'Unfeature' : 'Feature'}
                      </button>

                      {/* Deprecate */}
                      {(skill as SkillSummary & { status?: string }).status !== 'deprecated' &&
                        (skill as SkillSummary & { status?: string }).status !== 'removed' && (
                          <button
                            style={actionBtn('amber')}
                            onClick={() => setDeprecateTarget({ skill })}
                            data-testid={`deprecate-btn-${skill.slug}`}
                            aria-label={`Deprecate ${skill.name}`}
                          >
                            Deprecate
                          </button>
                        )}

                      {/* Remove — security team only */}
                      {isSecurityTeam &&
                        (skill as SkillSummary & { status?: string }).status !== 'removed' && (
                          <button
                            style={actionBtn('red')}
                            onClick={() => setRemoveTarget({ skill })}
                            data-testid={`remove-btn-${skill.slug}`}
                            aria-label={`Remove ${skill.name}`}
                          >
                            Remove
                          </button>
                        )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '10px',
            marginTop: '20px',
          }}
        >
          <button
            disabled={page <= 1}
            style={chipStyle(page <= 1)}
            onClick={() => setPage(Math.max(1, page - 1))}
            aria-label="Previous page"
          >
            Prev
          </button>
          <span style={{ color: C.muted, fontSize: '12px' }}>
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            style={chipStyle(page >= totalPages)}
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            aria-label="Next page"
          >
            Next
          </button>
        </div>
      )}

      {/* Deprecate Confirm Dialog */}
      {deprecateTarget && (
        <AdminConfirmDialog
          title="Deprecate Skill"
          message={`Are you sure you want to deprecate "${deprecateTarget.skill.name}"? Users will still be able to view it but it will be marked as deprecated.`}
          confirmLabel="Deprecate"
          destructive={false}
          onConfirm={handleDeprecateConfirm}
          onCancel={() => setDeprecateTarget(null)}
        />
      )}

      {/* Remove Confirm Dialog */}
      {removeTarget && (
        <AdminConfirmDialog
          title="Remove Skill"
          message={`Warning: This will permanently remove "${removeTarget.skill.name}" from the marketplace. This action is irreversible and is logged for audit purposes. Are you sure?`}
          confirmLabel="Remove"
          destructive={true}
          onConfirm={handleRemoveConfirm}
          onCancel={() => setRemoveTarget(null)}
        />
      )}
    </div>
  );
}
