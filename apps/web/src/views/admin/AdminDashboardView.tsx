import { useMemo } from 'react';
import { useT } from '../../context/ThemeContext';
import { StatCard } from '../../components/admin/StatCard';
import { AreaChartBase } from '../../components/charts/AreaChartBase';
import { DivisionChartGrid } from '../../components/charts/DivisionChartGrid';
import { SubmissionFunnel } from '../../components/charts/SubmissionFunnel';
import { AdminLoadingSkeleton } from '../../components/admin/AdminLoadingSkeleton';
import { useChartTheme } from '../../hooks/useChartTheme';
import { useAdminDashboard } from '../../hooks/useAdminDashboard';

const DIVISION_COLORS: Record<string, string> = {
  'engineering-org': '#4b7dff',
  'product-org': '#1fd49e',
};

export function AdminDashboardView() {
  const C = useT();
  const ct = useChartTheme();
  const { summary, timeSeries, funnel, divisionData, loading, error } = useAdminDashboard();

  const sparkStub = useMemo(
    () => Array.from({ length: 7 }, () => ({ value: Math.floor(Math.random() * 40) + 10 })),
    [],
  );

  if (loading) {
    return <AdminLoadingSkeleton />;
  }

  if (error) {
    return (
      <div
        data-testid="dashboard-error"
        style={{
          padding: '24px',
          borderRadius: '8px',
          background: C.adminBg,
          color: C.red,
          border: `1px solid ${C.border}`,
        }}
      >
        <strong>Failed to load dashboard:</strong> {error}
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: C.text, margin: 0 }}>Dashboard</h1>
        <span style={{ fontFamily: 'Outfit, sans-serif', fontSize: '11px', fontWeight: 400, color: C.dim }}>
          Live data
        </span>
      </div>

      {/* Stat cards grid */}
      <div
        data-testid="stat-cards-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '14px',
          marginBottom: '24px',
        }}
      >
        <StatCard label="Daily Active Users" value={summary.dau} delta={12} sparkData={sparkStub} color={C.accent} />
        <StatCard label="New Installs (7d)" value={summary.new_installs_7d} delta={8} sparkData={sparkStub} color={ct.seriesColors.installs} />
        <StatCard label="Active Installs" value={summary.active_installs} delta={3} sparkData={sparkStub} color={C.green} />
        <StatCard label="Published Skills" value={summary.published_skills} delta={5} color={C.purple} />
        <StatCard label="Pending Reviews" value={summary.pending_reviews} delta={-2} color={C.amber} />
        <StatCard label="Pass Rate" value={`${summary.submission_pass_rate}%`} delta={1} color={C.green} />
      </div>

      {/* Installs time series */}
      <div style={{ marginBottom: '24px' }} data-testid="charts-area">
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: C.text, marginBottom: '8px' }}>Installs Over Time</h2>
        <AreaChartBase
          data={timeSeries as unknown as Record<string, unknown>[]}
          series={[
            { key: 'installs', color: ct.seriesColors.installs, name: 'Installs' },
            { key: 'users', color: ct.seriesColors.views, name: 'Users' },
          ]}
          height={260}
        />
      </div>

      {/* Division chart grid */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: C.text, marginBottom: '8px' }}>By Division</h2>
        <DivisionChartGrid data={divisionData} colors={DIVISION_COLORS} />
      </div>

      {/* Submission funnel */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: C.text, marginBottom: '8px' }}>Submission Funnel (30d)</h2>
        <SubmissionFunnel
          submitted={funnel.submitted}
          gate1={funnel.gate1_passed}
          gate2={funnel.gate2_passed}
          approved={funnel.approved}
          published={funnel.published}
        />
      </div>
    </div>
  );
}
