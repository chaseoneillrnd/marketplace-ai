import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function RequireAdmin() {
  const { user } = useAuth();
  if (!user?.is_platform_team) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
