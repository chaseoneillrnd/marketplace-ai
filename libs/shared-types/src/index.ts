/** Shared TypeScript types matching the SkillHub API schemas. */

// --- Skill Domain ---

export interface SkillSummary {
  id: string;
  slug: string;
  name: string;
  short_desc: string;
  category: string;
  divisions: string[];
  tags: string[];
  author: string | null;
  author_type: string;
  version: string;
  install_method: string;
  verified: boolean;
  featured: boolean;
  install_count: number;
  fork_count: number;
  favorite_count: number;
  avg_rating: number;
  review_count: number;
  days_ago: number | null;
  user_has_installed?: boolean | null;
  user_has_favorited?: boolean | null;
}

export interface TriggerPhrase {
  id: string;
  phrase: string;
}

export interface SkillVersion {
  id: string;
  version: string;
  content: string;
  frontmatter: Record<string, unknown> | null;
  changelog: string | null;
  published_at: string;
}

export interface SkillDetail {
  id: string;
  slug: string;
  name: string;
  short_desc: string;
  category: string;
  divisions: string[];
  tags: string[];
  author: string | null;
  author_id: string;
  author_type: string;
  current_version: string;
  install_method: string;
  data_sensitivity: string;
  external_calls: boolean;
  verified: boolean;
  featured: boolean;
  status: string;
  install_count: number;
  fork_count: number;
  favorite_count: number;
  view_count: number;
  review_count: number;
  avg_rating: number;
  trending_score: number;
  published_at: string | null;
  deprecated_at: string | null;
  trigger_phrases: TriggerPhrase[];
  current_version_content: SkillVersion | null;
  user_has_installed?: boolean | null;
  user_has_favorited?: boolean | null;
}

export interface SkillBrowseResponse {
  items: SkillSummary[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export type SortOption = 'trending' | 'installs' | 'rating' | 'newest' | 'updated';

// --- Auth Domain ---

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserClaims {
  user_id: string;
  email: string;
  name: string;
  username: string;
  division: string;
  role: string;
  is_platform_team: boolean;
  is_security_team: boolean;
  iat: number;
  exp: number;
}

// --- Social Domain ---

export interface InstallResponse {
  id: string;
  skill_id: string;
  user_id: string;
  version: string;
  method: string;
  installed_at: string;
}

export interface FavoriteResponse {
  user_id: string;
  skill_id: string;
  created_at: string;
}

export interface ForkResponse {
  id: string;
  original_skill_id: string;
  forked_skill_id: string;
  forked_skill_slug: string;
  forked_by: string;
}

export interface ReviewResponse {
  id: string;
  skill_id: string;
  user_id: string;
  rating: number;
  body: string;
  helpful_count: number;
  unhelpful_count: number;
  created_at: string;
  updated_at: string;
}

export interface ReviewListResponse {
  items: ReviewResponse[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface CommentReply {
  id: string;
  comment_id: string;
  user_id: string;
  body: string;
  deleted_at: string | null;
  created_at: string;
}

export interface CommentResponse {
  id: string;
  skill_id: string;
  user_id: string;
  body: string;
  upvote_count: number;
  deleted_at: string | null;
  created_at: string;
  replies: CommentReply[];
}

export interface CommentListResponse {
  items: CommentResponse[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// --- Feature Flags Domain ---

export interface FlagsResponse {
  flags: Record<string, boolean>;
}

// --- Admin Domain ---

export interface FeatureSkillRequest {
  featured: boolean;
  featured_order?: number | null;
}

export interface FeatureSkillResponse {
  slug: string;
  featured: boolean;
  featured_order: number | null;
}

export interface DeprecateSkillResponse {
  slug: string;
  status: string;
  deprecated_at: string | null;
}

export interface RemoveSkillResponse {
  slug: string;
  status: string;
}

export interface AuditLogEntry {
  id: string;
  event_type: string;
  actor_id: string | null;
  actor_name: string | null;
  target_type: string | null;
  target_id: string | null;
  metadata: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// --- Constants ---

export const CATEGORIES = [
  'All', 'Engineering', 'Product', 'Data', 'Security',
  'Finance', 'General', 'HR', 'Research',
] as const;

export const DIVISIONS = [
  'Engineering Org', 'Product Org', 'Finance & Legal', 'People & HR',
  'Operations', 'Executive Office', 'Sales & Marketing', 'Customer Success',
] as const;

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'trending', label: 'Trending' },
  { value: 'installs', label: 'Most Installed' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'newest', label: 'Newest' },
  { value: 'updated', label: 'Recently Updated' },
];

export const INSTALL_LABELS: Record<string, string> = {
  'claude-code': 'Claude Code',
  'mcp': 'MCP Server',
  'manual': 'Manual',
};

export const DIVISION_COLORS: Record<string, string> = {
  'Engineering Org': '#4b7dff',
  'Product Org': '#a78bfa',
  'Finance & Legal': '#1fd49e',
  'People & HR': '#f2a020',
  'Operations': '#22d3ee',
  'Executive Office': '#ef5060',
  'Sales & Marketing': '#fb923c',
  'Customer Success': '#84cc16',
  // Slug-keyed aliases (API returns slugs)
  'engineering-org': '#4b7dff',
  'product-org': '#a78bfa',
  'finance-legal': '#1fd49e',
  'people-hr': '#f2a020',
  'operations': '#22d3ee',
  'executive-office': '#ef5060',
  'sales-marketing': '#fb923c',
  'customer-success': '#84cc16',
};

/** Map display category names to API slugs (matches categories.slug in DB). */
export const CATEGORY_SLUG_MAP: Record<string, string> = {
  Engineering: 'engineering',
  Product: 'product',
  Data: 'data',
  Security: 'security',
  Finance: 'finance',
  General: 'general',
  HR: 'hr',
  Research: 'research',
  Operations: 'operations',
};

/** Map display division names to API slugs (matches divisions.slug in DB). */
export const DIVISION_SLUG_MAP: Record<string, string> = {
  'Engineering Org': 'engineering-org',
  'Product Org': 'product-org',
  'Finance & Legal': 'finance-legal',
  'People & HR': 'people-hr',
  'Operations': 'operations',
  'Executive Office': 'executive-office',
  'Sales & Marketing': 'sales-marketing',
  'Customer Success': 'customer-success',
};

/** Reverse map: API slug → display name (for rendering API responses). */
export const DIVISION_NAME_MAP: Record<string, string> = Object.fromEntries(
  Object.entries(DIVISION_SLUG_MAP).map(([name, slug]) => [slug, name]),
);

export const OAUTH_PROVIDERS = [
  { id: 'microsoft', label: 'Microsoft / Azure AD', color: '#0078d4', hint: 'Most common for enterprise orgs' },
  { id: 'google', label: 'Google Workspace', color: '#4285f4', hint: 'G Suite / Google Cloud identity' },
  { id: 'okta', label: 'Okta', color: '#007dc1', hint: 'Okta Universal Directory' },
  { id: 'github', label: 'GitHub Enterprise', color: '#555', hint: 'Org-level GitHub SSO' },
  { id: 'oidc', label: 'Generic OIDC / SAML', color: '#a78bfa', hint: 'Any standards-compliant provider' },
] as const;
