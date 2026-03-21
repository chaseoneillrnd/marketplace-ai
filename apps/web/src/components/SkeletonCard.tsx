import { useT } from '../context/ThemeContext';

export function SkeletonCard() {
  const C = useT();
  const bar = (w: string, h = '12px') => (
    <div
      data-testid="skeleton-bar"
      style={{
        width: w,
        height: h,
        borderRadius: '4px',
        background: C.border,
        animation: 'pulse 1.5s ease-in-out infinite',
      }}
    />
  );

  return (
    <div
      data-testid="skeleton-card"
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: '12px',
        overflow: 'hidden',
      }}
    >
      <div style={{ height: '3px', background: C.border }} />
      <div style={{ padding: '16px' }}>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '14px' }}>
          <div style={{ width: '38px', height: '38px', borderRadius: '8px', background: C.border }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {bar('140px', '14px')}
            {bar('60px', '10px')}
          </div>
        </div>
        {bar('100%', '12px')}
        <div style={{ height: '6px' }} />
        {bar('75%', '12px')}
        <div style={{ height: '14px' }} />
        <div style={{ display: 'flex', gap: '4px' }}>
          {bar('70px', '18px')}
          {bar('70px', '18px')}
        </div>
        <div style={{ height: '14px' }} />
        <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: '10px', display: 'flex', justifyContent: 'space-between' }}>
          {bar('80px')}
          {bar('60px')}
        </div>
      </div>
      <style>{`@keyframes pulse{0%,100%{opacity:.4}50%{opacity:.8}}`}</style>
    </div>
  );
}
