import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../lib/api';
import { ModeSelector } from '../../components/submit/ModeSelector';
import { SubmissionStatusTracker } from '../../components/submit/SubmissionStatusTracker';

export type SubmitMode = 'form' | 'upload' | 'mcp';

export interface SubmitPayload {
  frontMatter: Record<string, unknown>;
  content: string;
}

export function SubmitSkillPage() {
  const C = useT();
  const { isAuthenticated } = useAuth();
  const [mode, setMode] = useState<SubmitMode>('form');
  const [submitted, setSubmitted] = useState(false);
  const [submissionId, setSubmissionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (data: SubmitPayload) => {
    setError(null);
    setSubmitting(true);
    try {
      const result = await api.post<{ display_id: string }>('/api/v1/submissions', {
        name: data.frontMatter.name ?? '',
        short_desc: data.frontMatter.short_desc ?? '',
        category: data.frontMatter.category ?? '',
        content: data.content,
        declared_divisions: data.frontMatter.declared_divisions ?? [],
        division_justification: data.frontMatter.division_justification ?? '',
      });
      setSubmissionId(result.display_id);
      setSubmitted(true);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Submission failed';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div style={{ padding: '60px 24px', textAlign: 'center', color: C.muted }}>
        <h2 style={{ color: C.text, marginBottom: '8px' }}>Sign in required</h2>
        <p>You must be signed in to submit a skill.</p>
      </div>
    );
  }

  if (submitted && submissionId) {
    return <SubmissionStatusTracker displayId={submissionId} />;
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '32px 24px' }}>
      <h1
        style={{
          fontSize: '24px',
          fontWeight: 700,
          color: C.text,
          marginBottom: '4px',
        }}
      >
        Submit a Skill
      </h1>
      <p style={{ fontSize: '14px', color: C.muted, marginBottom: '24px' }}>
        Share your Claude skill with the organization.
      </p>

      <ModeSelector mode={mode} onModeChange={setMode} />

      {error && (
        <div
          role="alert"
          style={{
            marginTop: '16px',
            padding: '12px 16px',
            borderRadius: '8px',
            background: C.redDim ?? 'rgba(255,59,48,0.1)',
            color: C.red ?? '#ff3b30',
            fontSize: '13px',
          }}
        >
          {error}
        </div>
      )}

      <div style={{ marginTop: '24px' }}>
        {mode === 'form' && (
          <FormBuilderPlaceholder onSubmit={handleSubmit} submitting={submitting} />
        )}
        {mode === 'upload' && (
          <UploadPlaceholder onSubmit={handleSubmit} submitting={submitting} />
        )}
        {mode === 'mcp' && (
          <MCPPlaceholder onSubmit={handleSubmit} submitting={submitting} />
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Placeholder mode components — will be replaced with full versions  */
/* ------------------------------------------------------------------ */

function FormBuilderPlaceholder({
  onSubmit,
  submitting,
}: {
  onSubmit: (data: SubmitPayload) => void;
  submitting: boolean;
}) {
  const C = useT();
  const [name, setName] = useState('');
  const [shortDesc, setShortDesc] = useState('');
  const [category, setCategory] = useState('coding');
  const [content, setContent] = useState('');

  const handleClick = () => {
    onSubmit({
      frontMatter: { name, short_desc: shortDesc, category, declared_divisions: [], division_justification: '' },
      content,
    });
  };

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    fontSize: '13px',
    borderRadius: '8px',
    border: `1px solid ${C.border}`,
    background: C.surface,
    color: C.text,
    outline: 'none',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column' as const, gap: '16px' }}>
      <label style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
        Skill Name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. PR Review Assistant"
          style={{ ...inputStyle, marginTop: '6px' }}
          data-testid="skill-name-input"
        />
      </label>
      <label style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
        Short Description
        <input
          value={shortDesc}
          onChange={(e) => setShortDesc(e.target.value)}
          placeholder="One-line summary"
          style={{ ...inputStyle, marginTop: '6px' }}
          data-testid="skill-desc-input"
        />
      </label>
      <label style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
        Category
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          style={{ ...inputStyle, marginTop: '6px' }}
          data-testid="skill-category-select"
        >
          {['coding', 'writing', 'analysis', 'automation', 'data', 'design', 'devops', 'security', 'testing', 'other'].map(
            (c) => (
              <option key={c} value={c}>
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </option>
            ),
          )}
        </select>
      </label>
      <label style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
        SKILL.md Content
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={10}
          placeholder="Paste your SKILL.md content here..."
          style={{ ...inputStyle, marginTop: '6px', resize: 'vertical' as const }}
          data-testid="skill-content-textarea"
        />
      </label>
      <button
        onClick={handleClick}
        disabled={submitting}
        data-testid="submit-skill-button"
        style={{
          padding: '10px 20px',
          fontSize: '14px',
          fontWeight: 600,
          borderRadius: '8px',
          border: 'none',
          background: C.accent,
          color: '#fff',
          cursor: submitting ? 'not-allowed' : 'pointer',
          opacity: submitting ? 0.6 : 1,
          alignSelf: 'flex-start',
        }}
      >
        {submitting ? 'Submitting...' : 'Submit Skill'}
      </button>
    </div>
  );
}

function UploadPlaceholder({
  onSubmit: _onSubmit,
  submitting: _submitting,
}: {
  onSubmit: (data: SubmitPayload) => void;
  submitting: boolean;
}) {
  const C = useT();
  return (
    <div
      data-testid="upload-mode"
      style={{
        padding: '48px',
        border: `2px dashed ${C.border}`,
        borderRadius: '12px',
        textAlign: 'center',
        color: C.muted,
      }}
    >
      <p style={{ fontSize: '14px', fontWeight: 600 }}>Upload .md</p>
      <p style={{ fontSize: '13px', marginTop: '8px' }}>
        Drag and drop a SKILL.md file here, or click to browse.
      </p>
      <p style={{ fontSize: '12px', marginTop: '12px', color: C.dim }}>
        Coming soon in a future update.
      </p>
    </div>
  );
}

function MCPPlaceholder({
  onSubmit: _onSubmit,
  submitting: _submitting,
}: {
  onSubmit: (data: SubmitPayload) => void;
  submitting: boolean;
}) {
  const C = useT();
  return (
    <div
      data-testid="mcp-mode"
      style={{
        padding: '48px',
        border: `2px dashed ${C.border}`,
        borderRadius: '12px',
        textAlign: 'center',
        color: C.muted,
      }}
    >
      <p style={{ fontSize: '14px', fontWeight: 600 }}>MCP Sync</p>
      <p style={{ fontSize: '13px', marginTop: '8px' }}>
        Connect to an MCP server and sync skills automatically.
      </p>
      <p style={{ fontSize: '12px', marginTop: '12px', color: C.dim }}>
        Coming soon in a future update.
      </p>
    </div>
  );
}
