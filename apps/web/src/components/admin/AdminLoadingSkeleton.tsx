import { useT } from '../../context/ThemeContext';

export function AdminLoadingSkeleton() {
  const C = useT();
  const sidebarWidth = C.adminSidebarWidth ?? '240px';

  const barStyle = (width: string): React.CSSProperties => ({
    height: 14,
    borderRadius: 6,
    width,
    background: C.border,
    animation: 'adminPulse 1.4s ease-in-out infinite',
  });

  return (
    <>
      <style>{`
        @keyframes adminPulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
      `}</style>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <div
          data-testid="admin-loading-sidebar"
          style={{
            width: sidebarWidth,
            minWidth: sidebarWidth,
            background: C.adminSurfaceSide,
            padding: 24,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {Array.from({ length: 6 }, (_, i) => (
            <div
              key={i}
              data-testid="admin-loading-bar"
              style={barStyle(i % 2 === 0 ? '80%' : '60%')}
            />
          ))}
        </div>
        <div
          data-testid="admin-loading-content"
          style={{
            flex: 1,
            background: C.adminBg,
            padding: 32,
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
          }}
        >
          <div data-testid="admin-loading-bar" style={barStyle('40%')} />
          <div data-testid="admin-loading-bar" style={barStyle('70%')} />
          <div data-testid="admin-loading-bar" style={barStyle('55%')} />
          <div data-testid="admin-loading-bar" style={barStyle('85%')} />
          <div data-testid="admin-loading-bar" style={barStyle('30%')} />
        </div>
      </div>
    </>
  );
}
