import { NavLink } from 'react-router-dom';
import { useT } from '../../context/ThemeContext';

const NAV_ITEMS = [
  { icon: '\u{1F4CA}', label: 'Dashboard', to: '/admin', end: true },
  { icon: '\u{1F4DD}', label: 'Queue', to: '/admin/queue' },
  { icon: '\u{1F4AC}', label: 'Feedback', to: '/admin/feedback' },
  { icon: '\u2699', label: 'Skills', to: '/admin/skills' },
  { icon: '\u{1F3F3}', label: 'Feature Flags', to: '/admin/flags' },
  { icon: '\u{1F5FA}', label: 'Roadmap', to: '/admin/roadmap' },
  { icon: '\u2193', label: 'Export', to: '/admin/export' },
];

export function AdminSideNav() {
  const C = useT();
  const sidebarWidth = C.adminSidebarWidth ?? '240px';

  return (
    <nav
      style={{
        width: sidebarWidth,
        minWidth: sidebarWidth,
        background: C.adminSurfaceSide,
        borderRight: `1px solid ${C.border}`,
        padding: '24px 0',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: C.dim,
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
          padding: '0 20px',
          marginBottom: 8,
        }}
      >
        NAVIGATION
      </div>
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 20px',
            textDecoration: 'none',
            borderLeft: isActive ? `3px solid ${C.accent}` : '3px solid transparent',
            background: isActive ? C.accentDim : 'transparent',
            color: isActive ? C.accent : C.muted,
            fontWeight: isActive ? 600 : 400,
            fontSize: 14,
            transition: 'background 0.15s, color 0.15s',
          })}
        >
          <span role="img" aria-hidden="true">
            {item.icon}
          </span>
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
