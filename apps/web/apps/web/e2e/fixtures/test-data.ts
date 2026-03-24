/**
 * Shared test data constants for E2E tests.
 */

export const API_BASE = 'http://localhost:8000';

/** Stub user credentials — password is always 'user' */
export const USERS = {
  /** Platform team admin (alice) */
  alice: { username: 'alice', password: 'user', division: 'platform_team', isAdmin: true },
  /** Data science regular user (bob) */
  bob: { username: 'bob', password: 'user', division: 'data_science', isAdmin: false },
  /** Security team user (carol) */
  carol: { username: 'carol', password: 'user', division: 'security_team', isAdmin: false },
  /** Regular user (dave) */
  dave: { username: 'dave', password: 'user', division: 'regular', isAdmin: false },
} as const;

export type StubUser = keyof typeof USERS;

/** Category names shown in the UI */
export const CATEGORIES = [
  'All', 'Engineering', 'Product', 'Data', 'Security',
  'Finance', 'General', 'HR', 'Research',
] as const;

/** Division names shown in the UI */
export const DIVISIONS = [
  'Engineering Org', 'Product Org', 'Finance & Legal', 'People & HR',
  'Operations', 'Executive Office', 'Sales & Marketing', 'Customer Success',
] as const;

/** Sort options available in the UI */
export const SORT_OPTIONS = [
  { value: 'trending', label: 'Trending' },
  { value: 'installs', label: 'Most Installed' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'newest', label: 'Newest' },
  { value: 'updated', label: 'Recently Updated' },
] as const;
