import { describe, it, expect, vi } from 'vitest';
import { render, screen, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { FileUploadMode } from '../FileUploadMode';
import { parseFrontMatter } from '../FileUploadMode';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('FileUploadMode', () => {
  it('renders drop zone initially', () => {
    render(<FileUploadMode onSubmit={vi.fn()} />, { wrapper });
    expect(screen.getByTestId('file-upload-mode')).toBeInTheDocument();
    expect(screen.getByTestId('drop-zone')).toBeInTheDocument();
    expect(screen.getByText('Drop SKILL.md here')).toBeInTheDocument();
  });

  it('shows error for non-.md files', async () => {
    render(<FileUploadMode onSubmit={vi.fn()} />, { wrapper });
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByTestId('file-input');
    // Manually fire change event since accept filter may block userEvent.upload
    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });
    expect(screen.getByTestId('upload-error')).toHaveTextContent('Only .md files are accepted');
  });

  it('parses a valid .md file with front matter', async () => {
    const user = userEvent.setup();
    render(<FileUploadMode onSubmit={vi.fn()} />, { wrapper });
    const mdContent = `---
name: Test Skill
description: A test skill for validation
category: coding
---
# Hello

This is the content.`;
    const file = new File([mdContent], 'SKILL.md', { type: 'text/markdown' });
    const input = screen.getByTestId('file-input');
    await user.upload(input, file);
    // After upload, should show validator and preview
    await screen.findByTestId('front-matter-validator');
    expect(screen.getByTestId('skill-preview-panel')).toBeInTheDocument();
  });

  it('shows Edit and Submit buttons after parsing', async () => {
    const user = userEvent.setup();
    render(<FileUploadMode onSubmit={vi.fn()} />, { wrapper });
    const mdContent = `---
name: Test Skill
description: A test skill for validation
---
Content here.`;
    const file = new File([mdContent], 'SKILL.md', { type: 'text/markdown' });
    await user.upload(screen.getByTestId('file-input'), file);
    await screen.findByTestId('btn-edit');
    expect(screen.getByTestId('btn-submit')).toBeInTheDocument();
  });

  it('shows edit textarea when Edit clicked', async () => {
    const user = userEvent.setup();
    render(<FileUploadMode onSubmit={vi.fn()} />, { wrapper });
    const mdContent = `---
name: Test Skill
description: A test skill for validation
---
Content here.`;
    const file = new File([mdContent], 'SKILL.md', { type: 'text/markdown' });
    await user.upload(screen.getByTestId('file-input'), file);
    await screen.findByTestId('btn-edit');
    await user.click(screen.getByTestId('btn-edit'));
    expect(screen.getByTestId('edit-textarea')).toBeInTheDocument();
    expect(screen.getByTestId('btn-save-edit')).toBeInTheDocument();
  });

  it('handles drag over state', () => {
    render(<FileUploadMode onSubmit={vi.fn()} />, { wrapper });
    const dropZone = screen.getByTestId('drop-zone');
    fireEvent.dragOver(dropZone, { dataTransfer: { files: [] } });
    // Drop zone should visually react (we just verify no crash)
    fireEvent.dragLeave(dropZone);
  });

  it('handles file drop', async () => {
    render(<FileUploadMode onSubmit={vi.fn()} />, { wrapper });
    const mdContent = `---
name: Dropped Skill
description: A skill dropped into the zone
---
Dropped content.`;
    const file = new File([mdContent], 'SKILL.md', { type: 'text/markdown' });
    const dropZone = screen.getByTestId('drop-zone');
    await act(async () => {
      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file] },
      });
    });
    await screen.findByTestId('front-matter-validator');
  });
});

describe('parseFrontMatter', () => {
  it('parses YAML front matter and content', () => {
    const input = `---
name: Test
description: A description
---
Body content here`;
    const result = parseFrontMatter(input);
    expect(result.frontMatter.name).toBe('Test');
    expect(result.frontMatter.description).toBe('A description');
    expect(result.content).toBe('Body content here');
  });

  it('handles missing front matter', () => {
    const result = parseFrontMatter('Just plain content');
    expect(result.frontMatter).toEqual({});
    expect(result.content).toBe('Just plain content');
  });

  it('parses inline arrays', () => {
    const input = `---
tags: [python, ai, testing]
name: Test
---
Content`;
    const result = parseFrontMatter(input);
    expect(result.frontMatter.tags).toEqual(['python', 'ai', 'testing']);
  });

  it('parses YAML list arrays', () => {
    const input = `---
tags:
  - python
  - ai
name: Test
---
Content`;
    const result = parseFrontMatter(input);
    expect(result.frontMatter.tags).toEqual(['python', 'ai']);
    expect(result.frontMatter.name).toBe('Test');
  });

  it('strips quotes from values', () => {
    const input = `---
name: "Quoted Name"
description: 'Single quoted'
---
Content`;
    const result = parseFrontMatter(input);
    expect(result.frontMatter.name).toBe('Quoted Name');
    expect(result.frontMatter.description).toBe('Single quoted');
  });
});
