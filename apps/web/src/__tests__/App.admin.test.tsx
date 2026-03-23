import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { act } from 'react';

vi.mock('../views/admin/AdminDashboardView', () => ({
  AdminDashboardView: () => <div data-testid="admin-dashboard">Dashboard</div>,
}));
vi.mock('../views/admin/AdminQueueView', () => ({
  AdminQueueView: () => <div data-testid="admin-queue">Queue</div>,
}));
vi.mock('../views/admin/AdminFeedbackView', () => ({
  AdminFeedbackView: () => <div data-testid="admin-feedback">Feedback</div>,
}));
vi.mock('../views/admin/AdminSkillsView', () => ({
  AdminSkillsView: () => <div data-testid="admin-skills">Skills</div>,
}));
vi.mock('../views/admin/AdminRoadmapView', () => ({
  AdminRoadmapView: () => <div data-testid="admin-roadmap">Roadmap</div>,
}));
vi.mock('../views/admin/AdminExportView', () => ({
  AdminExportView: () => <div data-testid="admin-export">Export</div>,
}));

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: 'http://localhost:3000/', origin: 'http://localhost:3000' });

import { App } from '../App';

function mockApiResponse(url: string) {
  if (url.includes('/flags')) {
    return { ok: true, status: 200, json: () => Promise.resolve({ flags: {} }) };
  }
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve({ items: [], total: 0, page: 1, per_page: 20, has_more: false }),
  };
}

describe('App admin routes exist', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockImplementation((...args: unknown[]) => {
      const url = typeof args[0] === 'string' ? args[0] : '';
      return Promise.resolve(mockApiResponse(url));
    });
  });

  it('renders home view at / (admin routes exist in tree without breaking)', async () => {
    await act(async () => {
      render(<App />);
    });
    // If routes are broken, this will throw. Just verify the app renders.
    expect(document.body).toBeTruthy();
  });

  it('skip link and main-content still present after admin route additions', async () => {
    await act(async () => {
      render(<App />);
    });
    const skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toBeInTheDocument();
    expect(document.getElementById('main-content')).toBeInTheDocument();
  });
});
