import { useState, useEffect } from 'react';
import { useT } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../lib/api';
import { ModeSelector } from '../../components/submit/ModeSelector';
import { SubmissionStatusTracker } from '../../components/submit/SubmissionStatusTracker';
import { FormBuilderMode } from '../../components/submit/FormBuilderMode';
import { FileUploadMode } from '../../components/submit/FileUploadMode';
import { MCPSyncMode } from '../../components/submit/MCPSyncMode';

const CATEGORIES = ['coding', 'writing', 'analysis', 'automation', 'data', 'design', 'devops', 'security', 'testing', 'other'];

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
  const [divisions, setDivisions] = useState<string[]>([]);

  useEffect(() => {
    api.get<{ name: string; slug: string }[]>('/api/v1/divisions').then((data) => {
      setDivisions(data.map((d) => d.slug));
    }).catch(() => {});
  }, []);

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
          <FormBuilderMode onSubmit={handleSubmit} categories={CATEGORIES} divisions={divisions} />
        )}
        {mode === 'upload' && (
          <FileUploadMode onSubmit={handleSubmit} />
        )}
        {mode === 'mcp' && (
          <MCPSyncMode onSubmit={handleSubmit} />
        )}
      </div>
    </div>
  );
}
