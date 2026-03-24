import { useEffect, useRef, useState } from 'react';
import { useT } from '../../context/ThemeContext';

interface Props {
  frontMatter: Record<string, unknown>;
  content: string;
}

function toYaml(obj: Record<string, unknown>): string {
  const lines: string[] = [];
  for (const [key, value] of Object.entries(obj)) {
    if (value === undefined || value === null || value === '') continue;
    if (Array.isArray(value)) {
      if (value.length === 0) continue;
      lines.push(`${key}:`);
      for (const item of value) {
        lines.push(`  - ${String(item)}`);
      }
    } else {
      lines.push(`${key}: ${String(value)}`);
    }
  }
  return lines.join('\n');
}

export function SkillPreviewPanel({ frontMatter, content }: Props) {
  const C = useT();
  const [rendered, setRendered] = useState({ yaml: '', body: '' });
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setRendered({
        yaml: toYaml(frontMatter),
        body: content,
      });
    }, 500);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [frontMatter, content]);

  return (
    <div
      data-testid="skill-preview-panel"
      style={{
        border: `1px solid ${C.border}`,
        borderRadius: '10px',
        overflow: 'hidden',
        maxHeight: '400px',
        overflowY: 'auto',
        background: C.surface,
      }}
    >
      <div
        style={{
          padding: '8px 14px',
          background: C.surfaceHi,
          borderBottom: `1px solid ${C.border}`,
          fontSize: '11px',
          fontWeight: 600,
          color: C.muted,
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        SKILL.md Preview
      </div>
      {rendered.yaml && (
        <pre
          data-testid="preview-frontmatter"
          style={{
            margin: 0,
            padding: '14px',
            background: C.codeBg,
            borderBottom: `1px solid ${C.border}`,
            fontSize: '12px',
            lineHeight: '1.6',
            color: C.accent,
            fontFamily: "'JetBrains Mono', monospace",
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {'---\n'}{rendered.yaml}{'\n---'}
        </pre>
      )}
      <div
        data-testid="preview-content"
        style={{
          padding: '14px',
          fontSize: '13px',
          lineHeight: '1.7',
          color: C.text,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {rendered.body || <span style={{ color: C.dim, fontStyle: 'italic' }}>No content yet...</span>}
      </div>
    </div>
  );
}
