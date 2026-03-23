import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import type { SkillSummary } from '@skillhub/shared-types';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { FlagsProvider } from '../context/FlagsContext';
import { AnnouncerProvider } from '../context/AnnouncerContext';
import { SkillCard } from '../components/SkillCard';
import { DivisionChip } from '../components/DivisionChip';
import { AuthModal } from '../components/AuthModal';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: 'http://localhost:3000/', origin: 'http://localhost:3000' });

const MOCK_SKILL: SkillSummary = {
  id: '00000000-0000-0000-0000-000000000001',
  slug: 'test-skill',
  name: 'Test Skill',
  short_desc: 'A test skill for accessibility checks',
  category: 'Engineering',
  divisions: ['engineering-org'],
  tags: ['test', 'a11y'],
  author: 'Test Author',
  author_type: 'community',
  version: '1.0.0',
  install_method: 'claude-code',
  verified: false,
  featured: false,
  install_count: 42,
  fork_count: 3,
  favorite_count: 7,
  avg_rating: 4.5,
  review_count: 10,
  days_ago: 1,
};

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>
        <AuthProvider>
          <FlagsProvider>
            <AnnouncerProvider>{children}</AnnouncerProvider>
          </FlagsProvider>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

beforeEach(() => {
  mockFetch.mockReset();
  mockFetch.mockImplementation((url: string) => {
    if (typeof url === 'string' && url.includes('/auth/dev-users')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ items: [], total: 0, page: 1, per_page: 20, has_more: false, flags: {} }),
    });
  });
});

describe('SkillCard Accessibility', () => {
  it('has role="article"', () => {
    render(<SkillCard skill={MOCK_SKILL} onClick={vi.fn()} />, { wrapper });
    const card = screen.getByRole('article');
    expect(card).toBeInTheDocument();
  });

  it('has tabIndex=0', () => {
    render(<SkillCard skill={MOCK_SKILL} onClick={vi.fn()} />, { wrapper });
    const card = screen.getByRole('article');
    expect(card).toHaveAttribute('tabindex', '0');
  });

  it('calls onClick when Enter key pressed', () => {
    const onClick = vi.fn();
    render(<SkillCard skill={MOCK_SKILL} onClick={onClick} />, { wrapper });
    const card = screen.getByRole('article');
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(onClick).toHaveBeenCalledWith(MOCK_SKILL);
  });

  it('calls onClick when Space key pressed', () => {
    const onClick = vi.fn();
    render(<SkillCard skill={MOCK_SKILL} onClick={onClick} />, { wrapper });
    const card = screen.getByRole('article');
    fireEvent.keyDown(card, { key: ' ' });
    expect(onClick).toHaveBeenCalledWith(MOCK_SKILL);
  });

  it('does not call onClick for other keys', () => {
    const onClick = vi.fn();
    render(<SkillCard skill={MOCK_SKILL} onClick={onClick} />, { wrapper });
    const card = screen.getByRole('article');
    fireEvent.keyDown(card, { key: 'Tab' });
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe('DivisionChip Accessibility', () => {
  it('has no tabIndex when onClick not provided', () => {
    render(<DivisionChip division="engineering-org" />, { wrapper });
    const chip = screen.getByText('Engineering Org');
    expect(chip).not.toHaveAttribute('tabindex');
  });

  it('has tabIndex=0 when onClick provided', () => {
    render(<DivisionChip division="engineering-org" onClick={vi.fn()} />, { wrapper });
    const chip = screen.getByRole('button');
    expect(chip).toHaveAttribute('tabindex', '0');
  });

  it('calls onClick when Enter pressed (interactive)', () => {
    const onClick = vi.fn();
    render(<DivisionChip division="engineering-org" onClick={onClick} />, { wrapper });
    const chip = screen.getByRole('button');
    fireEvent.keyDown(chip, { key: 'Enter' });
    expect(onClick).toHaveBeenCalled();
  });

  it('calls onClick when Space pressed (interactive)', () => {
    const onClick = vi.fn();
    render(<DivisionChip division="engineering-org" onClick={onClick} />, { wrapper });
    const chip = screen.getByRole('button');
    fireEvent.keyDown(chip, { key: ' ' });
    expect(onClick).toHaveBeenCalled();
  });
});

describe('AuthModal Accessibility', () => {
  it('has role="dialog"', () => {
    render(<AuthModal onClose={vi.fn()} />, { wrapper });
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
  });

  it('has aria-modal="true"', () => {
    render(<AuthModal onClose={vi.fn()} />, { wrapper });
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });
});
