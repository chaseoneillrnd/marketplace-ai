import { describe, it, expect, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { SkillPreviewPanel } from '../SkillPreviewPanel';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('SkillPreviewPanel', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the preview panel container', () => {
    render(
      <SkillPreviewPanel frontMatter={{ name: 'Test' }} content="Hello" />,
      { wrapper }
    );
    expect(screen.getByTestId('skill-preview-panel')).toBeInTheDocument();
  });

  it('shows SKILL.md Preview header', () => {
    render(
      <SkillPreviewPanel frontMatter={{ name: 'Test' }} content="Hello" />,
      { wrapper }
    );
    expect(screen.getByText('SKILL.md Preview')).toBeInTheDocument();
  });

  it('renders front matter as YAML after debounce', async () => {
    render(
      <SkillPreviewPanel
        frontMatter={{ name: 'My Skill', description: 'A test skill' }}
        content="Some content"
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(550);
    });
    const fmBlock = screen.getByTestId('preview-frontmatter');
    expect(fmBlock).toHaveTextContent('name: My Skill');
    expect(fmBlock).toHaveTextContent('description: A test skill');
    expect(fmBlock).toHaveTextContent('---');
  });

  it('renders content body after debounce', async () => {
    render(
      <SkillPreviewPanel frontMatter={{ name: 'Test' }} content="This is the body content" />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(550);
    });
    expect(screen.getByTestId('preview-content')).toHaveTextContent('This is the body content');
  });

  it('renders array values in YAML format', async () => {
    render(
      <SkillPreviewPanel
        frontMatter={{ name: 'Test', tags: ['python', 'ai'] }}
        content="Content"
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(550);
    });
    const fmBlock = screen.getByTestId('preview-frontmatter');
    expect(fmBlock).toHaveTextContent('tags:');
    expect(fmBlock).toHaveTextContent('- python');
    expect(fmBlock).toHaveTextContent('- ai');
  });

  it('shows placeholder when content is empty', () => {
    render(
      <SkillPreviewPanel frontMatter={{}} content="" />,
      { wrapper }
    );
    expect(screen.getByText('No content yet...')).toBeInTheDocument();
  });

  it('skips empty/null front matter values', async () => {
    render(
      <SkillPreviewPanel
        frontMatter={{ name: 'Test', empty: '', nothing: null }}
        content="Content"
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(550);
    });
    const fmBlock = screen.getByTestId('preview-frontmatter');
    expect(fmBlock).toHaveTextContent('name: Test');
    expect(fmBlock.textContent).not.toContain('empty:');
    expect(fmBlock.textContent).not.toContain('nothing:');
  });
});
