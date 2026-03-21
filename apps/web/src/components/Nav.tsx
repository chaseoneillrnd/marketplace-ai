import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useT, useTheme } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';

interface Props {
  onAuthOpen: () => void;
}

export function Nav({ onAuthOpen }: Props) {
  const C = useT();
  const { isDark, toggle } = useTheme();
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [focused, setFocused] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const navItem = (label: string, path: string) => {
    const active = location.pathname === path;
    return (
      <button
        key={path}
        onClick={() => navigate(path)}
        style={{
          background: active ? C.border : 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: active ? 600 : 400,
          color: active ? C.text : C.muted,
          padding: '4px 10px',
          borderRadius: '6px',
          transition: 'all 0.15s',
        }}
      >
        {label}
      </button>
    );
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: C.navBg,
        backdropFilter: 'blur(14px)',
        borderBottom: `1px solid ${C.border}`,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        gap: '14px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginRight: '6px', cursor: 'pointer' }} onClick={() => navigate('/')}>
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            background: C.accent,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
          }}
        >
          &#9889;
        </div>
        <span style={{ fontWeight: 700, fontSize: '15px', color: C.text }}>SkillHub</span>
        <span
          style={{
            fontSize: '10px',
            padding: '1px 6px',
            borderRadius: '4px',
            background: C.accentDim,
            color: C.accent,
            fontFamily: "'JetBrains Mono',monospace",
          }}
        >
          INTERNAL
        </span>
      </div>

      <div style={{ display: 'flex', gap: '2px' }}>
        {navItem('Discover', '/')}
        {navItem('Browse', '/browse')}
        {navItem('Filtered', '/filtered')}
      </div>

      <div style={{ flex: 1, maxWidth: '380px', marginLeft: 'auto', marginRight: 'auto', position: 'relative' }}>
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Search skills..."
          style={{
            width: '100%',
            background: focused ? C.surfaceHi : C.surface,
            border: `1px solid ${focused ? C.accent + '66' : C.border}`,
            borderRadius: '8px',
            padding: '8px 14px',
            fontSize: '13px',
            color: C.text,
            outline: 'none',
            transition: 'all 0.15s',
            boxShadow: focused ? `0 0 0 3px ${C.accentDim}` : 'none',
          }}
        />
      </div>

      <div style={{ display: 'flex', gap: '10px', marginLeft: 'auto', alignItems: 'center' }}>
        {/* Theme toggle */}
        <button
          onClick={toggle}
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          style={{
            width: '38px',
            height: '22px',
            borderRadius: '11px',
            border: 'none',
            cursor: 'pointer',
            position: 'relative',
            flexShrink: 0,
            transition: 'background 0.3s',
            background: isDark ? '#152030' : '#c8d5e6',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '3px',
              left: isDark ? '3px' : '19px',
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: isDark ? '#4b7dff' : '#ffffff',
              boxShadow: `0 1px 4px rgba(0,0,0,${isDark ? 0.5 : 0.25})`,
              transition: 'left 0.25s cubic-bezier(.4,0,.2,1), background 0.3s',
            }}
          />
        </button>

        {isAuthenticated && user ? (
          <>
            <button
              onClick={() => navigate('/submit')}
              style={{
                padding: '5px 12px',
                fontSize: '12px',
                borderRadius: '8px',
                border: `1px solid ${C.border}`,
                background: C.surface,
                color: C.muted,
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              + Submit
            </button>
            <div ref={menuRef} style={{ position: 'relative' }}>
              <div
                onClick={() => setMenuOpen(!menuOpen)}
                data-testid="user-menu-trigger"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  padding: '4px 10px 4px 4px',
                  borderRadius: '99px',
                  border: `1px solid ${menuOpen ? C.borderHi : C.border}`,
                  background: menuOpen ? C.surfaceHi : C.surface,
                  transition: 'all 0.15s',
                }}
              >
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: 'hsl(200,45%,30%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '10px',
                    fontWeight: 700,
                    color: 'hsl(200,60%,85%)',
                  }}
                >
                  {user.name
                    .split(' ')
                    .map((n: string) => n[0])
                    .join('')}
                </div>
                <div style={{ lineHeight: 1.2 }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: C.text }}>{user.name.split(' ')[0]}</div>
                  <div data-testid="nav-division" style={{ fontSize: '9px', color: C.dim, fontFamily: "'JetBrains Mono',monospace" }}>
                    {user.division}
                  </div>
                </div>
              </div>
              {menuOpen && (
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: 'calc(100% + 8px)',
                    width: '220px',
                    zIndex: 200,
                    background: C.surface,
                    border: `1px solid ${C.borderHi}`,
                    borderRadius: '12px',
                    boxShadow: C.cardShadow,
                    overflow: 'hidden',
                  }}
                >
                  <div style={{ padding: '14px 16px', borderBottom: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>{user.name}</div>
                    <div style={{ fontSize: '11px', color: C.dim }}>{user.role} &middot; {user.division}</div>
                    <div style={{ fontSize: '11px', color: C.dim, marginTop: '4px', fontFamily: "'JetBrains Mono',monospace" }}>
                      {user.email}
                    </div>
                  </div>
                  <div style={{ borderTop: `1px solid ${C.border}`, padding: '6px 0' }}>
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        logout();
                        navigate('/');
                      }}
                      style={{
                        display: 'flex',
                        gap: '10px',
                        width: '100%',
                        padding: '10px 16px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '13px',
                        color: C.red,
                        textAlign: 'left',
                      }}
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <button
            onClick={onAuthOpen}
            style={{
              padding: '5px 12px',
              fontSize: '12px',
              borderRadius: '8px',
              border: 'none',
              background: C.accent,
              color: '#fff',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Sign In
          </button>
        )}
      </div>
    </div>
  );
}
