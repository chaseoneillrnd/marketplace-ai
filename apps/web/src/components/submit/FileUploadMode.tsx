import { useCallback, useState, type DragEvent } from 'react';
import { useT } from '../../context/ThemeContext';
import { FrontMatterValidator } from './FrontMatterValidator';
import { SkillPreviewPanel } from './SkillPreviewPanel';

interface Props {
  onSubmit: (data: { frontMatter: Record<string, unknown>; content: string }) => void;
}

function parseFrontMatter(text: string): { frontMatter: Record<string, unknown>; content: string } {
  const fmRegex = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/;
  const match = text.match(fmRegex);
  if (!match) {
    return { frontMatter: {}, content: text };
  }

  const yamlBlock = match[1];
  const body = match[2];
  const frontMatter: Record<string, unknown> = {};

  let currentKey = '';
  let currentArray: string[] | null = null;

  for (const line of yamlBlock.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    const arrayItemMatch = trimmed.match(/^-\s+(.+)$/);
    if (arrayItemMatch && currentKey) {
      if (!currentArray) {
        currentArray = [];
      }
      currentArray.push(arrayItemMatch[1].trim());
      frontMatter[currentKey] = currentArray;
      continue;
    }

    if (currentArray) {
      currentArray = null;
    }

    const kvMatch = trimmed.match(/^(\w[\w-]*)\s*:\s*(.*)$/);
    if (kvMatch) {
      currentKey = kvMatch[1];
      const val = kvMatch[2].trim();
      if (val === '') {
        frontMatter[currentKey] = '';
      } else if (val.startsWith('[') && val.endsWith(']')) {
        frontMatter[currentKey] = val
          .slice(1, -1)
          .split(',')
          .map((s) => s.trim().replace(/^['"]|['"]$/g, ''))
          .filter(Boolean);
      } else {
        frontMatter[currentKey] = val.replace(/^['"]|['"]$/g, '');
      }
    }
  }

  return { frontMatter, content: body.trim() };
}

export { parseFrontMatter };

export function FileUploadMode({ onSubmit }: Props) {
  const C = useT();
  const [dragging, setDragging] = useState(false);
  const [parsed, setParsed] = useState<{ frontMatter: Record<string, unknown>; content: string } | null>(null);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [valid, setValid] = useState(false);

  const handleFile = useCallback((file: File) => {
    setError('');
    if (!file.name.endsWith('.md')) {
      setError('Only .md files are accepted');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result;
      if (typeof text !== 'string') {
        setError('Failed to read file');
        return;
      }
      const result = parseFrontMatter(text);
      setParsed(result);
      setEditContent(text);
    };
    reader.readAsText(file);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleSaveEdit = () => {
    const result = parseFrontMatter(editContent);
    setParsed(result);
    setEditing(false);
  };

  const handleSubmit = () => {
    if (parsed) {
      onSubmit(parsed);
    }
  };

  return (
    <div data-testid="file-upload-mode">
      {!parsed ? (
        <>
          <div
            data-testid="drop-zone"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            style={{
              border: `2px dashed ${dragging ? C.accent : C.border}`,
              borderRadius: '12px',
              padding: '48px 24px',
              textAlign: 'center',
              background: dragging ? C.accentDim : 'transparent',
              transition: 'all 0.2s',
              cursor: 'pointer',
            }}
            onClick={() => document.getElementById('file-upload-input')?.click()}
          >
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>
              {dragging ? '\u2B07' : '\u{1F4C4}'}
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: C.text, marginBottom: '4px' }}>
              Drop SKILL.md here
            </div>
            <div style={{ fontSize: '12px', color: C.muted }}>
              or click to browse
            </div>
            <input
              id="file-upload-input"
              data-testid="file-input"
              type="file"
              accept=".md"
              onChange={handleInputChange}
              style={{ display: 'none' }}
            />
          </div>
          {error && (
            <div data-testid="upload-error" style={{ color: C.red, fontSize: '12px', marginTop: '8px' }}>
              {error}
            </div>
          )}
        </>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {editing ? (
            <div>
              <textarea
                data-testid="edit-textarea"
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={16}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '12px',
                  fontFamily: "'JetBrains Mono', monospace",
                  lineHeight: '1.6',
                  background: C.inputBg,
                  border: `1px solid ${C.border}`,
                  borderRadius: '8px',
                  color: C.text,
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
              <button
                data-testid="btn-save-edit"
                type="button"
                onClick={handleSaveEdit}
                style={{
                  marginTop: '8px',
                  padding: '6px 16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: 'none',
                  background: C.accent,
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                Save Changes
              </button>
            </div>
          ) : (
            <>
              <FrontMatterValidator frontMatter={parsed.frontMatter} onChange={setValid} />
              <SkillPreviewPanel frontMatter={parsed.frontMatter} content={parsed.content} />
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  data-testid="btn-edit"
                  type="button"
                  onClick={handleEdit}
                  style={{
                    padding: '8px 20px',
                    fontSize: '12px',
                    fontWeight: 600,
                    borderRadius: '8px',
                    border: `1px solid ${C.border}`,
                    background: 'transparent',
                    color: C.text,
                    cursor: 'pointer',
                  }}
                >
                  Edit
                </button>
                <button
                  data-testid="btn-submit"
                  type="button"
                  disabled={!valid}
                  onClick={handleSubmit}
                  style={{
                    padding: '8px 20px',
                    fontSize: '12px',
                    fontWeight: 600,
                    borderRadius: '8px',
                    border: 'none',
                    background: valid ? C.green : C.border,
                    color: valid ? '#fff' : C.dim,
                    cursor: valid ? 'pointer' : 'default',
                  }}
                >
                  Submit
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
