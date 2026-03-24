import { useEffect, useRef, useState } from 'react';
import { useT } from '../../context/ThemeContext';

const VALID_CATEGORIES = [
  'coding',
  'writing',
  'analysis',
  'automation',
  'data',
  'design',
  'devops',
  'security',
  'testing',
  'other',
];

interface FieldResult {
  valid: boolean;
  message: string;
}

function validateName(value: unknown): FieldResult {
  if (typeof value !== 'string' || value.trim().length === 0) {
    return { valid: false, message: 'Name is required' };
  }
  if (value.trim().length < 3) {
    return { valid: false, message: 'Name must be at least 3 characters' };
  }
  if (value.trim().length > 100) {
    return { valid: false, message: 'Name must be 100 characters or fewer' };
  }
  return { valid: true, message: 'Valid' };
}

function validateDescription(value: unknown): FieldResult {
  if (typeof value !== 'string' || value.trim().length === 0) {
    return { valid: false, message: 'Description is required' };
  }
  if (value.trim().length < 10) {
    return { valid: false, message: 'Description must be at least 10 characters' };
  }
  if (value.trim().length > 500) {
    return { valid: false, message: 'Description must be 500 characters or fewer' };
  }
  return { valid: true, message: 'Valid' };
}

function validateCategory(value: unknown): FieldResult {
  if (value === undefined || value === null || value === '') {
    return { valid: true, message: 'Optional' };
  }
  if (typeof value !== 'string' || !VALID_CATEGORIES.includes(value)) {
    return { valid: false, message: `Invalid category. Must be one of: ${VALID_CATEGORIES.join(', ')}` };
  }
  return { valid: true, message: 'Valid' };
}

function validateTags(value: unknown): FieldResult {
  if (value === undefined || value === null) {
    return { valid: true, message: 'Optional' };
  }
  if (!Array.isArray(value)) {
    return { valid: false, message: 'Tags must be an array of strings' };
  }
  if (!value.every((t) => typeof t === 'string')) {
    return { valid: false, message: 'Each tag must be a string' };
  }
  return { valid: true, message: 'Valid' };
}

interface ValidationResults {
  name: FieldResult;
  description: FieldResult;
  category: FieldResult;
  tags: FieldResult;
}

function validate(frontMatter: Record<string, unknown>): ValidationResults {
  return {
    name: validateName(frontMatter.name),
    description: validateDescription(frontMatter.description),
    category: validateCategory(frontMatter.category),
    tags: validateTags(frontMatter.tags),
  };
}

interface Props {
  frontMatter: Record<string, unknown>;
  onChange?: (valid: boolean) => void;
}

export { VALID_CATEGORIES };

export function FrontMatterValidator({ frontMatter, onChange }: Props) {
  const C = useT();
  const [results, setResults] = useState<ValidationResults>(() => validate(frontMatter));
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      const r = validate(frontMatter);
      setResults(r);
      const allValid = Object.values(r).every((f) => f.valid);
      onChange?.(allValid);
    }, 300);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [frontMatter, onChange]);

  const fields: { key: keyof ValidationResults; label: string; required: boolean }[] = [
    { key: 'name', label: 'Name', required: true },
    { key: 'description', label: 'Description', required: true },
    { key: 'category', label: 'Category', required: false },
    { key: 'tags', label: 'Tags', required: false },
  ];

  return (
    <div data-testid="front-matter-validator" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {fields.map(({ key, label, required }) => {
        const r = results[key];
        return (
          <div
            key={key}
            data-testid={`field-${key}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 10px',
              borderRadius: '6px',
              background: r.valid ? `${C.green}10` : `${C.red}10`,
              border: `1px solid ${r.valid ? `${C.green}30` : `${C.red}30`}`,
            }}
          >
            <span
              data-testid={`icon-${key}`}
              style={{
                fontSize: '14px',
                color: r.valid ? C.green : C.red,
                fontWeight: 700,
                width: '18px',
                textAlign: 'center',
              }}
            >
              {r.valid ? '\u2713' : '\u2717'}
            </span>
            <span style={{ fontSize: '12px', fontWeight: 600, color: C.text, minWidth: '80px' }}>
              {label}
              {required && <span style={{ color: C.red, marginLeft: '2px' }}>*</span>}
            </span>
            <span style={{ fontSize: '11px', color: r.valid ? C.muted : C.red }}>
              {r.message}
            </span>
          </div>
        );
      })}
    </div>
  );
}
