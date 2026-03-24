import { describe, it, expect, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { FrontMatterValidator } from '../FrontMatterValidator';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('FrontMatterValidator', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders all four validation fields', () => {
    render(
      <FrontMatterValidator frontMatter={{ name: '', description: '' }} />,
      { wrapper }
    );
    expect(screen.getByTestId('front-matter-validator')).toBeInTheDocument();
    expect(screen.getByTestId('field-name')).toBeInTheDocument();
    expect(screen.getByTestId('field-description')).toBeInTheDocument();
    expect(screen.getByTestId('field-category')).toBeInTheDocument();
    expect(screen.getByTestId('field-tags')).toBeInTheDocument();
  });

  it('shows invalid state for empty required fields after debounce', async () => {
    render(
      <FrontMatterValidator frontMatter={{ name: '', description: '' }} />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-name')).toHaveTextContent('\u2717');
    expect(screen.getByTestId('icon-description')).toHaveTextContent('\u2717');
  });

  it('shows valid state for correct required fields after debounce', async () => {
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'My Skill', description: 'A valid description here' }}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-name')).toHaveTextContent('\u2713');
    expect(screen.getByTestId('icon-description')).toHaveTextContent('\u2713');
  });

  it('validates name minimum length', async () => {
    render(
      <FrontMatterValidator frontMatter={{ name: 'ab', description: 'A valid description here' }} />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-name')).toHaveTextContent('\u2717');
  });

  it('validates name maximum length', async () => {
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'a'.repeat(101), description: 'A valid description here' }}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-name')).toHaveTextContent('\u2717');
  });

  it('validates description minimum length', async () => {
    render(
      <FrontMatterValidator frontMatter={{ name: 'My Skill', description: 'short' }} />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-description')).toHaveTextContent('\u2717');
  });

  it('accepts valid category', async () => {
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'My Skill', description: 'A valid description', category: 'coding' }}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-category')).toHaveTextContent('\u2713');
  });

  it('rejects invalid category', async () => {
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'My Skill', description: 'A valid description', category: 'invalid-cat' }}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-category')).toHaveTextContent('\u2717');
  });

  it('accepts valid tags array', async () => {
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'My Skill', description: 'A valid description', tags: ['python', 'ai'] }}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-tags')).toHaveTextContent('\u2713');
  });

  it('rejects non-array tags', async () => {
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'My Skill', description: 'A valid description', tags: 'not-array' }}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(screen.getByTestId('icon-tags')).toHaveTextContent('\u2717');
  });

  it('calls onChange with validity state after debounce', async () => {
    const onChange = vi.fn();
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'My Skill', description: 'A valid description here' }}
        onChange={onChange}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('calls onChange with false when invalid', async () => {
    const onChange = vi.fn();
    render(
      <FrontMatterValidator
        frontMatter={{ name: '', description: '' }}
        onChange={onChange}
      />,
      { wrapper }
    );
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it('debounces validation (does not fire immediately)', async () => {
    const onChange = vi.fn();
    render(
      <FrontMatterValidator
        frontMatter={{ name: 'My Skill', description: 'A valid description here' }}
        onChange={onChange}
      />,
      { wrapper }
    );
    // Before debounce timeout
    expect(onChange).not.toHaveBeenCalled();
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    expect(onChange).toHaveBeenCalled();
  });
});
