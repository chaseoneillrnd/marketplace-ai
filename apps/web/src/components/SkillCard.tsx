import { useState } from 'react';
import type { SkillSummary } from '@skillhub/shared-types';
import { INSTALL_LABELS, DIVISION_COLORS } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { DivisionChip } from './DivisionChip';
import { INSTALL_COLORS } from '../lib/theme';

const TAG_HUES = ['#4b7dff', '#a78bfa', '#1fd49e', '#f2a020', '#22d3ee', '#ef5060', '#fb923c', '#e879f9'];

interface Props {
  skill: SkillSummary;
  onClick: (skill: SkillSummary) => void;
}

export function SkillCard({ skill, onClick }: Props) {
  const C = useT();
  const [hov, setHov] = useState(false);
  const primaryDiv = skill.divisions[0];
  const accent = (primaryDiv && DIVISION_COLORS[primaryDiv]) ?? (skill.author_type === 'official' ? C.accent : C.green);

  return (
    <div
      data-testid="skill-card"
      onClick={() => onClick(skill)}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? C.surfaceHi : C.surface,
        border: `1px solid ${hov ? C.borderHi : C.border}`,
        borderRadius: '12px',
        overflow: 'hidden',
        cursor: 'pointer',
        transition: 'all 0.18s',
        transform: hov ? 'translateY(-2px)' : 'none',
        boxShadow: hov ? C.cardShadow : C.mode === 'light' ? '0 1px 4px rgba(0,0,0,0.07)' : 'none',
      }}
    >
      <div style={{ height: '3px', background: `linear-gradient(90deg,${accent},${accent}44)` }} />
      <div style={{ padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                background: `${accent}18`,
                border: `1px solid ${accent}30`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '17px',
                fontWeight: 800,
                color: accent,
                fontFamily: "'JetBrains Mono',monospace",
                flexShrink: 0,
              }}
            >
              {skill.name[0]}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ fontWeight: 600, fontSize: '14px', color: C.text }}>{skill.name}</span>
                {skill.verified && <span style={{ color: C.amber, fontSize: '11px' }}>&#10003;</span>}
              </div>
              <span style={{ fontSize: '10px', color: C.dim, fontFamily: "'JetBrains Mono',monospace" }}>
                v{skill.version}
              </span>
            </div>
          </div>
          <span
            style={{
              fontSize: '10px',
              padding: '2px 9px',
              borderRadius: '99px',
              background: `${accent}18`,
              color: accent,
              border: `1px solid ${accent}28`,
              fontWeight: 500,
              whiteSpace: 'nowrap',
            }}
          >
            {skill.author_type}
          </span>
        </div>
        <p style={{ fontSize: '12px', color: C.muted, lineHeight: '1.55', margin: '0 0 8px', minHeight: '36px' }}>
          {skill.short_desc}
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '8px' }}>
          {skill.divisions.slice(0, 2).map((d: string) => (
            <DivisionChip key={d} division={d} small />
          ))}
          {skill.divisions.length > 2 && (
            <span style={{ fontSize: '9px', color: C.dim, fontFamily: "'JetBrains Mono',monospace", padding: '2px 6px' }}>
              +{skill.divisions.length - 2}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '12px' }}>
          {skill.tags.slice(0, 3).map((t: string, i: number) => {
            const tagColor = TAG_HUES[i % TAG_HUES.length];
            return (
              <span
                key={t}
                style={{
                  fontSize: '10px',
                  padding: '2px 7px',
                  borderRadius: '4px',
                  background: `${tagColor}14`,
                  color: tagColor,
                  fontFamily: "'JetBrains Mono',monospace",
                }}
              >
                #{t}
              </span>
            );
          })}
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '10px',
            borderTop: `1px solid ${C.border}`,
          }}
        >
          <div style={{ display: 'flex', gap: '12px' }}>
            <span style={{ fontSize: '11px', color: C.muted }}>
              <span style={{ color: C.amber }}>&#9733;</span> {Number(skill.avg_rating).toFixed(1)}{' '}
              <span style={{ color: C.dim }}>({skill.review_count})</span>
            </span>
            <span style={{ fontSize: '11px', color: C.muted }}>&#8595; {skill.install_count.toLocaleString()}</span>
          </div>
          <span
            style={{
              fontSize: '10px',
              padding: '2px 8px',
              borderRadius: '4px',
              background: `${INSTALL_COLORS[skill.install_method] ?? C.accent}18`,
              color: INSTALL_COLORS[skill.install_method] ?? C.accent,
              fontFamily: "'JetBrains Mono',monospace",
            }}
          >
            {INSTALL_LABELS[skill.install_method] ?? skill.install_method}
          </span>
        </div>
      </div>
    </div>
  );
}
