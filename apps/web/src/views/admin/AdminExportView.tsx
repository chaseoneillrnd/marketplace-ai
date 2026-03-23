import { useT } from '../../context/ThemeContext';

export function AdminExportView() {
  const C = useT();
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: C.text }}>Export</h1>
      <p style={{ color: C.muted, fontSize: '14px' }}>Coming soon</p>
    </div>
  );
}
