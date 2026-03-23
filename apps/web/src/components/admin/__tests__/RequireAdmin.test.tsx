import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RequireAdmin } from '../RequireAdmin';

vi.mock('../../../hooks/useAuth');

import { useAuth } from '../../../hooks/useAuth';

const mockedUseAuth = vi.mocked(useAuth);

function renderWithRouter() {
  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <Routes>
        <Route path="/" element={<div data-testid="home">Home</div>} />
        <Route element={<RequireAdmin />}>
          <Route path="/admin" element={<div data-testid="admin">Admin</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('RequireAdmin', () => {
  it('renders Outlet when user.is_platform_team is true', () => {
    mockedUseAuth.mockReturnValue({
      user: { sub: '1', username: 'admin', division: 'eng', is_platform_team: true, exp: 0 } as any,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    });
    renderWithRouter();
    expect(screen.getByTestId('admin')).toBeInTheDocument();
  });

  it('redirects to / when user.is_platform_team is false', () => {
    mockedUseAuth.mockReturnValue({
      user: { sub: '2', username: 'user', division: 'eng', is_platform_team: false, exp: 0 } as any,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    });
    renderWithRouter();
    expect(screen.getByTestId('home')).toBeInTheDocument();
  });

  it('redirects to / when user is null', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
    });
    renderWithRouter();
    expect(screen.getByTestId('home')).toBeInTheDocument();
  });
});
