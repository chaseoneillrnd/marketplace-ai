import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminSideNav } from '../AdminSideNav';

function renderWithProviders() {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={['/admin']}>
        <AdminSideNav />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('AdminSideNav', () => {
  it('renders all 6 navigation items', () => {
    renderWithProviders();
    expect(screen.getByText('Dashboard')).toBeTruthy();
    expect(screen.getByText('Queue')).toBeTruthy();
    expect(screen.getByText('Feedback')).toBeTruthy();
    expect(screen.getByText('Skills')).toBeTruthy();
    expect(screen.getByText('Roadmap')).toBeTruthy();
    expect(screen.getByText('Export')).toBeTruthy();
  });

  it('renders emoji icons', () => {
    renderWithProviders();
    const icons = screen.getAllByRole('img', { hidden: true });
    expect(icons.length).toBeGreaterThanOrEqual(6);
  });

  it('renders the section label NAVIGATION', () => {
    renderWithProviders();
    expect(screen.getByText('NAVIGATION')).toBeTruthy();
  });

  it('all items are links', () => {
    renderWithProviders();
    const links = screen.getAllByRole('link');
    expect(links.length).toBe(6);
  });

  it('Dashboard link points to /admin', () => {
    renderWithProviders();
    const link = screen.getByText('Dashboard').closest('a');
    expect(link?.getAttribute('href')).toBe('/admin');
  });

  it('Queue link points to /admin/queue', () => {
    renderWithProviders();
    const link = screen.getByText('Queue').closest('a');
    expect(link?.getAttribute('href')).toBe('/admin/queue');
  });
});
