import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminLayout } from '../AdminLayout';

vi.mock('../AdminSideNav', () => ({
  AdminSideNav: () => <div data-testid="admin-side-nav" />,
}));

vi.mock('../AdminErrorBoundary', () => ({
  AdminErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="admin-error-boundary-wrapper">{children}</div>
  ),
}));

function renderWithProviders() {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<div data-testid="outlet-content">Outlet Here</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('AdminLayout', () => {
  it('renders the AdminSideNav inside the sidebar', () => {
    renderWithProviders();
    expect(screen.getByTestId('admin-side-nav')).toBeTruthy();
  });

  it('renders the AdminErrorBoundary wrapper around outlet', () => {
    renderWithProviders();
    expect(screen.getByTestId('admin-error-boundary-wrapper')).toBeTruthy();
  });

  it('renders the outlet content', () => {
    renderWithProviders();
    expect(screen.getByTestId('outlet-content')).toBeTruthy();
    expect(screen.getByText('Outlet Here')).toBeTruthy();
  });

  it('renders sidebar with data-testid="admin-sidebar"', () => {
    renderWithProviders();
    const sidebar = screen.getByTestId('admin-sidebar');
    expect(sidebar).toBeTruthy();
  });

  it('renders content area with data-testid="admin-content-area"', () => {
    renderWithProviders();
    const content = screen.getByTestId('admin-content-area');
    expect(content).toBeTruthy();
  });

  it('sidebar contains AdminSideNav', () => {
    renderWithProviders();
    const sidebar = screen.getByTestId('admin-sidebar');
    const nav = screen.getByTestId('admin-side-nav');
    expect(sidebar.contains(nav)).toBe(true);
  });

  it('content area contains AdminErrorBoundary with outlet', () => {
    renderWithProviders();
    const content = screen.getByTestId('admin-content-area');
    const boundary = screen.getByTestId('admin-error-boundary-wrapper');
    const outlet = screen.getByTestId('outlet-content');
    expect(content.contains(boundary)).toBe(true);
    expect(boundary.contains(outlet)).toBe(true);
  });
});
