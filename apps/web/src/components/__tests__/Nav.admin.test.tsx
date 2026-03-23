import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../context/ThemeContext';
import { Nav } from '../Nav';

const mockUseAuth = vi.fn();

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>{children}</ThemeProvider>
    </MemoryRouter>
  );
}

const baseUser = {
  user_id: 'u1',
  email: 'admin@test.com',
  name: 'Test User',
  username: 'testuser',
  division: 'Engineering Org',
  role: 'admin',
  is_security_team: false,
  iat: 0,
  exp: 999999999999,
};

describe('Nav Admin Link', () => {
  it('renders Admin link when user.is_platform_team is true', () => {
    mockUseAuth.mockReturnValue({
      user: { ...baseUser, is_platform_team: true },
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    });

    render(<Nav onAuthOpen={vi.fn()} />, { wrapper });
    const link = screen.getByRole('link', { name: 'Admin' });
    expect(link).toBeInTheDocument();
  });

  it('does not render Admin link when user.is_platform_team is false', () => {
    mockUseAuth.mockReturnValue({
      user: { ...baseUser, is_platform_team: false },
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    });

    render(<Nav onAuthOpen={vi.fn()} />, { wrapper });
    expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument();
  });

  it('does not render Admin link when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    render(<Nav onAuthOpen={vi.fn()} />, { wrapper });
    expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument();
  });

  it('Admin link points to /admin', () => {
    mockUseAuth.mockReturnValue({
      user: { ...baseUser, is_platform_team: true },
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    });

    render(<Nav onAuthOpen={vi.fn()} />, { wrapper });
    const link = screen.getByRole('link', { name: 'Admin' });
    expect(link).toHaveAttribute('href', '/admin');
  });
});
