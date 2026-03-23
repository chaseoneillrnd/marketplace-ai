import { Outlet } from 'react-router-dom';
import { useT } from '../../context/ThemeContext';
import { AdminSideNav } from './AdminSideNav';
import { AdminErrorBoundary } from './AdminErrorBoundary';

const NAV_HEIGHT = 60;

export function AdminLayout() {
  const C = useT();
  const sidebarWidth = C.adminSidebarWidth;

  return (
    <div style={{ display: 'flex', minHeight: `calc(100vh - ${NAV_HEIGHT}px)` }}>
      <div
        data-testid="admin-sidebar"
        style={{
          position: 'fixed',
          top: `${NAV_HEIGHT}px`,
          left: 0,
          width: sidebarWidth,
          height: `calc(100vh - ${NAV_HEIGHT}px)`,
          background: C.adminSurfaceSide,
          borderRight: `1px solid ${C.border}`,
          zIndex: 10,
          overflowY: 'auto',
        }}
      >
        <AdminSideNav />
      </div>
      <div
        data-testid="admin-content-area"
        style={{
          marginLeft: sidebarWidth,
          flex: 1,
          background: C.adminBg,
          padding: '32px 24px',
          minHeight: `calc(100vh - ${NAV_HEIGHT}px)`,
        }}
      >
        <AdminErrorBoundary>
          <Outlet />
        </AdminErrorBoundary>
      </div>
    </div>
  );
}
