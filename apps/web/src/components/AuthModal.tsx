import { useEffect, useState } from 'react';
import { OAUTH_PROVIDERS } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';
import { apiFetch } from '../lib/api';

interface StubUserInfo {
  username: string;
  name: string;
  division: string;
  role: string;
  is_platform_team: boolean;
  is_security_team: boolean;
}

interface Props {
  onClose: () => void;
}

export function AuthModal({ onClose }: Props) {
  const C = useT();
  const { login } = useAuth();
  const isDev = import.meta.env.DEV;

  // All hooks must be declared unconditionally
  const [error, setError] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState<string | null>(null);
  const [devUsers, setDevUsers] = useState<StubUserInfo[]>([]);
  const [step, setStep] = useState<'provider' | 'callback'>('provider');
  const [provider, setProvider] = useState<(typeof OAUTH_PROVIDERS)[number] | null>(null);

  // In dev mode, fetch the list of stub users from the API
  useEffect(() => {
    if (!isDev) return;
    apiFetch<StubUserInfo[]>('/auth/dev-users').then(setDevUsers).catch(() => {
      // Silently fail — dev users list is non-critical
    });
  }, [isDev]);

  const handleDevLogin = async (username: string) => {
    setLoadingUser(username);
    setError(null);
    try {
      await login(username, 'user');
      onClose();
    } catch {
      setError('Login failed. Please try again.');
    } finally {
      setLoadingUser(null);
    }
  };

  const getInitials = (name: string) =>
    name
      .split(' ')
      .map((w) => w[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);

  const handleProvider = (p: (typeof OAUTH_PROVIDERS)[number]) => {
    setProvider(p);
    setStep('callback');
  };

  // ---- Dev mode: show user picker directly ----
  if (isDev) {
    return (
      <div
        data-testid="auth-modal"
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(4,8,16,0.85)',
          backdropFilter: 'blur(10px)',
          zIndex: 999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        onClick={onClose}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            background: C.surface,
            border: `1px solid ${C.borderHi}`,
            borderRadius: '18px',
            width: '420px',
            maxHeight: '90vh',
            overflow: 'auto',
            boxShadow: C.cardShadow,
          }}
        >
          <div style={{ height: '3px', background: `linear-gradient(90deg,${C.accent},${C.purple},${C.green})` }} />
          <div style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '22px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: C.accent,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                }}
              >
                &#9889;
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '17px', color: C.text }}>Dev Sign In</div>
                <div style={{ fontSize: '12px', color: C.muted }}>Choose a test identity</div>
              </div>
            </div>

            <div
              style={{
                fontSize: '11px',
                color: C.dim,
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.9px',
                marginBottom: '10px',
              }}
            >
              Select user
            </div>

            {error && (
              <div
                style={{
                  padding: '8px 12px',
                  background: C.redDim,
                  borderRadius: '8px',
                  marginBottom: '10px',
                  fontSize: '12px',
                  color: C.red,
                }}
              >
                {error}
              </div>
            )}

            {devUsers.map((u) => {
              const isLoading = loadingUser === u.username;
              return (
                <button
                  key={u.username}
                  data-testid={`dev-user-${u.username}`}
                  onClick={() => handleDevLogin(u.username)}
                  disabled={isLoading}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 12px',
                    width: '100%',
                    background: C.bg,
                    border: `1px solid ${C.border}`,
                    borderRadius: '10px',
                    cursor: isLoading ? 'wait' : 'pointer',
                    textAlign: 'left',
                    marginBottom: '8px',
                    transition: 'all 0.12s',
                    opacity: isLoading ? 0.6 : 1,
                  }}
                >
                  <div
                    style={{
                      width: '34px',
                      height: '34px',
                      borderRadius: '50%',
                      background: u.is_platform_team
                        ? 'hsl(260,45%,35%)'
                        : u.is_security_team
                          ? 'hsl(0,45%,35%)'
                          : 'hsl(200,45%,30%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      fontWeight: 700,
                      color: 'hsl(200,60%,85%)',
                      flexShrink: 0,
                    }}
                  >
                    {getInitials(u.name)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>{u.name}</div>
                    <div style={{ fontSize: '11px', color: C.dim }}>
                      {u.role} &middot; {u.division}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '4px', flexShrink: 0 }}>
                    {u.is_platform_team && (
                      <span
                        style={{
                          fontSize: '9px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: 'hsl(260,40%,25%)',
                          color: 'hsl(260,60%,80%)',
                          fontWeight: 600,
                        }}
                      >
                        PLATFORM
                      </span>
                    )}
                    {u.is_security_team && (
                      <span
                        style={{
                          fontSize: '9px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: 'hsl(0,40%,25%)',
                          color: 'hsl(0,60%,80%)',
                          fontWeight: 600,
                        }}
                      >
                        SECURITY
                      </span>
                    )}
                  </div>
                </button>
              );
            })}

            <div
              style={{
                fontSize: '11px',
                color: C.dim,
                textAlign: 'center',
                marginTop: '12px',
                lineHeight: '1.5',
              }}
            >
              Dev mode &middot; password is &quot;user&quot; for all accounts
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---- Production mode: OAuth provider buttons ----
  return (
    <div
      data-testid="auth-modal"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,8,16,0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '18px',
          width: '420px',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: C.cardShadow,
        }}
      >
        <div style={{ height: '3px', background: `linear-gradient(90deg,${C.accent},${C.purple},${C.green})` }} />
        <div style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '22px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: C.accent,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px',
              }}
            >
              &#9889;
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '17px', color: C.text }}>Sign in to SkillHub</div>
              <div style={{ fontSize: '12px', color: C.muted }}>Use your organization's identity provider</div>
            </div>
          </div>

          {step === 'provider' && (
            <div>
              <div
                style={{
                  fontSize: '11px',
                  color: C.dim,
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.9px',
                  marginBottom: '10px',
                }}
              >
                Choose your provider
              </div>
              {OAUTH_PROVIDERS.map((p: (typeof OAUTH_PROVIDERS)[number]) => (
                <button
                  key={p.id}
                  onClick={() => handleProvider(p)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '11px 14px',
                    width: '100%',
                    background: C.bg,
                    border: `1px solid ${C.border}`,
                    borderRadius: '10px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    marginBottom: '8px',
                    transition: 'all 0.12s',
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>{p.label}</div>
                    <div style={{ fontSize: '11px', color: C.dim }}>{p.hint}</div>
                  </div>
                  <span style={{ fontSize: '16px', color: C.dim }}>&rarr;</span>
                </button>
              ))}
              <div
                style={{
                  fontSize: '11px',
                  color: C.dim,
                  textAlign: 'center',
                  marginTop: '12px',
                  lineHeight: '1.5',
                }}
              >
                SkillHub never stores your password &middot; Session expires after 8h
              </div>
            </div>
          )}

          {step === 'callback' && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: '14px', fontWeight: 600, color: C.text, marginBottom: '8px' }}>
                Redirecting to {provider?.label}&hellip;
              </div>
              <div style={{ fontSize: '12px', color: C.muted, marginBottom: '20px' }}>
                Complete sign-in in the popup window
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '6px' }}>
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: C.accent,
                      animation: `pulse 1.2s ease-in-out ${i * 0.3}s infinite`,
                    }}
                  />
                ))}
              </div>
              <style>{`@keyframes pulse{0%,100%{opacity:.2}50%{opacity:1}}`}</style>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
