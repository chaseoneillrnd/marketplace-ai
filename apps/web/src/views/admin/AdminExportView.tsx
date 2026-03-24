import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { useAdminExport } from '../../hooks/useAdminExport';

const SCOPES = ['installs', 'submissions', 'users', 'analytics'] as const;
const FORMATS = ['csv', 'json'] as const;

const SCOPE_LABELS: Record<string, string> = {
  installs: 'Installs',
  submissions: 'Submissions',
  users: 'Users',
  analytics: 'Analytics',
};

export function AdminExportView() {
  const C = useT();
  const [scope, setScope] = useState<string>('installs');
  const [format, setFormat] = useState<string>('csv');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const { exportStatus, loading, remainingExports, requestExport } = useAdminExport();

  const handleExport = () => {
    requestExport({
      scope,
      format,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
  };

  const btnGroupStyle = (active: boolean): React.CSSProperties => ({
    padding: '8px 16px',
    borderRadius: '99px',
    border: `1px solid ${active ? C.accent : C.border}`,
    background: active ? C.accentDim : 'transparent',
    color: active ? C.accent : C.muted,
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'Outfit, sans-serif',
    cursor: 'pointer',
    transition: 'all 0.15s',
  });

  const formatBtnStyle = (active: boolean): React.CSSProperties => ({
    padding: '7px 18px',
    borderRadius: '99px',
    border: `1px solid ${active ? C.accent : C.border}`,
    background: active ? C.accentDim : 'transparent',
    color: active ? C.accent : C.muted,
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'Outfit, sans-serif',
    cursor: 'pointer',
    transition: 'all 0.15s',
    textTransform: 'uppercase' as const,
  });

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px',
    borderRadius: '8px',
    border: `1px solid ${C.border}`,
    background: C.inputBg,
    color: C.text,
    fontSize: '13px',
    fontFamily: 'Outfit, sans-serif',
    outline: 'none',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: '11px',
    fontWeight: 600,
    fontFamily: 'Outfit, sans-serif',
    color: C.muted,
    marginBottom: '4px',
    letterSpacing: '0.3px',
  };

  return (
    <div data-testid="admin-export-view">
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px', color: C.text }}>Export</h1>

      {/* Scope selector */}
      <div style={{ marginBottom: '20px' }}>
        <div style={labelStyle}>Scope</div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {SCOPES.map((s) => (
            <button key={s} style={btnGroupStyle(scope === s)} onClick={() => setScope(s)}>
              {SCOPE_LABELS[s]}
            </button>
          ))}
        </div>
      </div>

      {/* Format toggle */}
      <div style={{ marginBottom: '20px' }}>
        <div style={labelStyle}>Format</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {FORMATS.map((f) => (
            <button key={f} style={formatBtnStyle(format === f)} onClick={() => setFormat(f)}>
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Date range */}
      <div style={{ display: 'flex', gap: '14px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <div>
          <label htmlFor="export-start" style={labelStyle}>Start Date</label>
          <input
            id="export-start"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={inputStyle}
          />
        </div>
        <div>
          <label htmlFor="export-end" style={labelStyle}>End Date</label>
          <input
            id="export-end"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={inputStyle}
          />
        </div>
      </div>

      {/* Request Export button */}
      <button
        onClick={handleExport}
        disabled={loading}
        style={{
          padding: '10px 24px',
          borderRadius: '99px',
          border: 'none',
          background: C.green,
          color: '#fff',
          fontSize: '13px',
          fontWeight: 600,
          fontFamily: 'Outfit, sans-serif',
          cursor: loading ? 'wait' : 'pointer',
          opacity: loading ? 0.7 : 1,
          transition: 'all 0.15s',
          marginBottom: '16px',
        }}
      >
        Request Export
      </button>

      {/* Rate limit */}
      <div style={{ fontSize: '12px', color: C.muted, marginBottom: '20px' }}>
        {remainingExports} of 5 exports remaining today
      </div>

      {/* Export status */}
      {exportStatus && (
        <div
          style={{
            background: C.surface,
            border: `1px solid ${C.border}`,
            borderRadius: '12px',
            padding: '16px',
          }}
        >
          {(exportStatus.status === 'pending' || exportStatus.status === 'processing') && (
            <div style={{ color: C.amber, fontSize: '13px', fontWeight: 500 }}>
              {'Processing... '}
              <span style={{ color: C.muted, fontSize: '11px' }}>This may take a moment</span>
            </div>
          )}
          {exportStatus.status === 'complete' && (
            <div>
              <span style={{ color: C.green, fontSize: '13px', fontWeight: 600 }}>Export complete!</span>
              {exportStatus.download_url && (
                <a
                  href={exportStatus.download_url}
                  style={{
                    display: 'inline-block',
                    marginLeft: '12px',
                    padding: '6px 16px',
                    borderRadius: '99px',
                    background: C.greenDim,
                    color: C.green,
                    fontSize: '12px',
                    fontWeight: 600,
                    textDecoration: 'none',
                    fontFamily: 'Outfit, sans-serif',
                  }}
                >
                  Download
                </a>
              )}
            </div>
          )}
          {exportStatus.status === 'failed' && (
            <div style={{ color: C.red, fontSize: '13px', fontWeight: 500 }}>
              Export failed. Please try again.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
