import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

// --- Types matching AdminDashboardView's usage ---

export interface DashboardSummary {
  dau: number;
  new_installs_7d: number;
  active_installs: number;
  published_skills: number;
  pending_reviews: number;
  submission_pass_rate: number;
  period: string;
}

export interface TimeSeriesPoint {
  date: string;
  installs: number;
  users: number;
  submissions: number;
  reviews: number;
}

export interface FunnelData {
  submitted: number;
  gate1_passed: number;
  gate2_passed: number;
  approved: number;
  published: number;
  gate1_rate: number;
  gate2_rate: number;
  approval_rate: number;
  period_days: number;
}

export interface TopSkill {
  slug: string;
  name: string;
  installs: number;
  rating: number;
}

export type DivisionData = Record<string, { date: string; value: number }[]>;

// --- API response wrappers ---

interface TimeSeriesApiResponse {
  series: TimeSeriesPoint[];
  days: number;
  division: string;
}

interface TopSkillsApiResponse {
  items: TopSkill[];
}

// --- Defaults (safe fallbacks when API returns nothing) ---

const DEFAULT_SUMMARY: DashboardSummary = {
  dau: 0,
  new_installs_7d: 0,
  active_installs: 0,
  published_skills: 0,
  pending_reviews: 0,
  submission_pass_rate: 0,
  period: '7d',
};

const DEFAULT_FUNNEL: FunnelData = {
  submitted: 0,
  gate1_passed: 0,
  gate2_passed: 0,
  approved: 0,
  published: 0,
  gate1_rate: 0,
  gate2_rate: 0,
  approval_rate: 0,
  period_days: 30,
};

/**
 * Derives per-division install data from the global time series.
 * The analytics API has no division-breakdown endpoint, so we use the
 * global installs series as a proxy for "engineering-org". When a
 * dedicated division endpoint is added, this transform can be replaced.
 */
function deriveDivisionData(series: TimeSeriesPoint[]): DivisionData {
  if (series.length === 0) return {};
  return {
    'engineering-org': series.map((p) => ({ date: p.date, value: p.installs })),
  };
}

export interface UseAdminDashboardResult {
  summary: DashboardSummary;
  timeSeries: TimeSeriesPoint[];
  funnel: FunnelData;
  topSkills: TopSkill[];
  divisionData: DivisionData;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useAdminDashboard(): UseAdminDashboardResult {
  const [summary, setSummary] = useState<DashboardSummary>(DEFAULT_SUMMARY);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>([]);
  const [funnel, setFunnel] = useState<FunnelData>(DEFAULT_FUNNEL);
  const [topSkills, setTopSkills] = useState<TopSkill[]>([]);
  const [divisionData, setDivisionData] = useState<DivisionData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [summaryData, timeSeriesData, funnelData, topSkillsData] =
        await Promise.all([
          api.get<DashboardSummary>('/api/v1/admin/analytics/summary').catch(() => null),
          api.get<TimeSeriesApiResponse>('/api/v1/admin/analytics/time-series').catch(() => null),
          api.get<FunnelData>('/api/v1/admin/analytics/submission-funnel').catch(() => null),
          api.get<TopSkillsApiResponse>('/api/v1/admin/analytics/top-skills').catch(() => null),
        ]);

      if (summaryData) setSummary(summaryData);
      const series = timeSeriesData?.series ?? [];
      setTimeSeries(series);
      setDivisionData(deriveDivisionData(series));
      if (funnelData) setFunnel(funnelData);
      setTopSkills(topSkillsData?.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    summary,
    timeSeries,
    funnel,
    topSkills,
    divisionData,
    loading,
    error,
    refresh: fetchAll,
  };
}
