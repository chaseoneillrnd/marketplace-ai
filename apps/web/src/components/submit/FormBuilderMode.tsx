import { useCallback, useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { FrontMatterValidator } from './FrontMatterValidator';
import { SkillPreviewPanel } from './SkillPreviewPanel';

interface Props {
  onSubmit: (data: { frontMatter: Record<string, unknown>; content: string }) => void;
  categories: string[];
  divisions: string[];
}

const STEPS = ['Name & Description', 'Content', 'Metadata', 'Review'];

function StepIndicator({ current, C }: { current: number; C: ReturnType<typeof useT> }) {
  return (
    <div data-testid="step-indicator" style={{ display: 'flex', gap: '4px', marginBottom: '24px' }}>
      {STEPS.map((label, i) => {
        const active = i === current;
        const completed = i < current;
        return (
          <div key={label} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div
              style={{
                height: '3px',
                borderRadius: '2px',
                background: active ? C.accent : completed ? C.green : C.border,
                transition: 'background 0.2s',
              }}
            />
            <span
              style={{
                fontSize: '10px',
                fontWeight: active ? 700 : 500,
                color: active ? C.accent : completed ? C.green : C.dim,
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              {i + 1}. {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function FormBuilderMode({ onSubmit, categories, divisions }: Props) {
  const C = useT();
  const [step, setStep] = useState(0);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [selectedDivisions, setSelectedDivisions] = useState<string[]>([]);
  const [tagsInput, setTagsInput] = useState('');
  const [frontMatterValid, setFrontMatterValid] = useState(false);

  const tags = tagsInput
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);

  const frontMatter: Record<string, unknown> = {
    name,
    description,
    ...(category ? { category } : {}),
    ...(tags.length > 0 ? { tags } : {}),
    ...(selectedDivisions.length > 0 ? { divisions: selectedDivisions } : {}),
  };

  const canNext = (): boolean => {
    if (step === 0) return name.trim().length >= 3 && description.trim().length >= 10;
    if (step === 1) return content.trim().length >= 50;
    if (step === 2) return true;
    return false;
  };

  const handleDivisionToggle = (div: string) => {
    setSelectedDivisions((prev) =>
      prev.includes(div) ? prev.filter((d) => d !== div) : [...prev, div]
    );
  };

  const handleValidationChange = useCallback((valid: boolean) => {
    setFrontMatterValid(valid);
  }, []);

  const handleSubmit = () => {
    onSubmit({ frontMatter, content });
  };

  const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    fontSize: '13px',
    background: C.inputBg,
    border: `1px solid ${C.border}`,
    borderRadius: '8px',
    color: C.text,
    outline: 'none',
    fontFamily: 'inherit',
    boxSizing: 'border-box' as const,
  };

  const labelStyle = {
    display: 'block',
    fontSize: '12px',
    fontWeight: 600 as const,
    color: C.text,
    marginBottom: '6px',
  };

  return (
    <div data-testid="form-builder-mode">
      <StepIndicator current={step} C={C} />

      {step === 0 && (
        <div data-testid="step-0" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={labelStyle}>
              Skill Name <span style={{ color: C.red }}>*</span>
            </label>
            <input
              data-testid="input-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Code Review Assistant"
              maxLength={100}
              style={inputStyle}
            />
            <div style={{ fontSize: '10px', color: C.dim, marginTop: '4px' }}>
              {name.trim().length}/100 characters (min 3)
            </div>
          </div>
          <div>
            <label style={labelStyle}>
              Description <span style={{ color: C.red }}>*</span>
            </label>
            <textarea
              data-testid="input-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this skill does..."
              maxLength={500}
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
            <div style={{ fontSize: '10px', color: C.dim, marginTop: '4px' }}>
              {description.trim().length}/500 characters (min 10)
            </div>
          </div>
        </div>
      )}

      {step === 1 && (
        <div data-testid="step-1">
          <label style={labelStyle}>
            Skill Content <span style={{ color: C.red }}>*</span>
          </label>
          <textarea
            data-testid="input-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your skill instructions in markdown..."
            rows={12}
            style={{
              ...inputStyle,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              lineHeight: '1.6',
              resize: 'vertical',
            }}
          />
          <div style={{ fontSize: '10px', color: content.trim().length >= 50 ? C.dim : C.red, marginTop: '4px' }}>
            {content.trim().length} characters (min 50)
          </div>
        </div>
      )}

      {step === 2 && (
        <div data-testid="step-2" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={labelStyle}>Category</label>
            <select
              data-testid="input-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{ ...inputStyle, cursor: 'pointer' }}
            >
              <option value="">Select a category...</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Divisions</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {divisions.map((div) => {
                const selected = selectedDivisions.includes(div);
                return (
                  <button
                    key={div}
                    data-testid={`division-${div}`}
                    type="button"
                    onClick={() => handleDivisionToggle(div)}
                    style={{
                      padding: '4px 12px',
                      fontSize: '11px',
                      borderRadius: '99px',
                      border: `1px solid ${selected ? C.accent : C.border}`,
                      background: selected ? C.accentDim : 'transparent',
                      color: selected ? C.accent : C.muted,
                      cursor: 'pointer',
                      fontWeight: selected ? 600 : 400,
                      transition: 'all 0.15s',
                    }}
                  >
                    {div}
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <label style={labelStyle}>Tags</label>
            <input
              data-testid="input-tags"
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="Comma-separated tags, e.g. python, code-review"
              style={inputStyle}
            />
            {tags.length > 0 && (
              <div style={{ display: 'flex', gap: '4px', marginTop: '6px', flexWrap: 'wrap' }}>
                {tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      fontSize: '10px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: `${C.accent}14`,
                      color: C.accent,
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {step === 3 && (
        <div data-testid="step-3" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <FrontMatterValidator frontMatter={frontMatter} onChange={handleValidationChange} />
          <SkillPreviewPanel frontMatter={frontMatter} content={content} />
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
        <button
          data-testid="btn-back"
          type="button"
          disabled={step === 0}
          onClick={() => setStep((s) => s - 1)}
          style={{
            padding: '8px 20px',
            fontSize: '12px',
            fontWeight: 600,
            borderRadius: '8px',
            border: `1px solid ${C.border}`,
            background: 'transparent',
            color: step === 0 ? C.dim : C.text,
            cursor: step === 0 ? 'default' : 'pointer',
            opacity: step === 0 ? 0.5 : 1,
          }}
        >
          Back
        </button>
        {step < 3 ? (
          <button
            data-testid="btn-next"
            type="button"
            disabled={!canNext()}
            onClick={() => setStep((s) => s + 1)}
            style={{
              padding: '8px 20px',
              fontSize: '12px',
              fontWeight: 600,
              borderRadius: '8px',
              border: 'none',
              background: canNext() ? C.accent : C.border,
              color: canNext() ? '#fff' : C.dim,
              cursor: canNext() ? 'pointer' : 'default',
            }}
          >
            Next
          </button>
        ) : (
          <button
            data-testid="btn-submit"
            type="button"
            disabled={!frontMatterValid}
            onClick={handleSubmit}
            style={{
              padding: '8px 20px',
              fontSize: '12px',
              fontWeight: 600,
              borderRadius: '8px',
              border: 'none',
              background: frontMatterValid ? C.green : C.border,
              color: frontMatterValid ? '#fff' : C.dim,
              cursor: frontMatterValid ? 'pointer' : 'default',
            }}
          >
            Submit
          </button>
        )}
      </div>
    </div>
  );
}
