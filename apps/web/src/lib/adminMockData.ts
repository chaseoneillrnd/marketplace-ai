export const MOCK_DASHBOARD_SUMMARY = {
  dau: 142,
  new_installs_7d: 87,
  active_installs: 1243,
  published_skills: 61,
  pending_reviews: 3,
  submission_pass_rate: 72.5,
  period: '7d',
};

export const MOCK_TIME_SERIES = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 86400000).toISOString().split('T')[0],
  installs: Math.floor(Math.random() * 20) + 5,
  users: Math.floor(Math.random() * 50) + 20,
  submissions: Math.floor(Math.random() * 5),
  reviews: Math.floor(Math.random() * 8),
}));

export const MOCK_FUNNEL = {
  submitted: 45,
  gate1_passed: 38,
  gate2_passed: 32,
  approved: 28,
  published: 28,
  gate1_rate: 84.4,
  gate2_rate: 84.2,
  approval_rate: 87.5,
  period_days: 30,
};

export const MOCK_TOP_SKILLS = [
  { slug: 'pr-review-assistant', name: 'PR Review Assistant', installs: 1842, rating: 4.9 },
  { slug: 'architecture-decision-record', name: 'Architecture Decision Record', installs: 743, rating: 4.8 },
  { slug: 'sql-query-optimizer', name: 'SQL Query Optimizer', installs: 1560, rating: 4.6 },
];

export const MOCK_DIVISION_DATA: Record<string, { date: string; value: number }[]> = {
  'engineering-org': Array.from({ length: 14 }, (_, i) => ({
    date: `2026-03-${String(i + 10).padStart(2, '0')}`,
    value: Math.floor(Math.random() * 30) + 10,
  })),
  'product-org': Array.from({ length: 14 }, (_, i) => ({
    date: `2026-03-${String(i + 10).padStart(2, '0')}`,
    value: Math.floor(Math.random() * 15) + 5,
  })),
};
