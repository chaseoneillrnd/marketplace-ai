import { useState, useEffect, useCallback } from 'react';
import type { SkillSummary } from '@skillhub/shared-types';
import { api } from '../lib/api';

export interface AdminSkillsResponse {
  items: SkillSummary[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export function useAdminSkills() {
  const [data, setData] = useState<AdminSkillsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const fetchSkills = useCallback(async (currentPage: number, currentSearch: string) => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        page: currentPage,
        per_page: 20,
      };
      if (currentSearch.trim()) {
        params.q = currentSearch.trim();
      }
      const result = await api.get<AdminSkillsResponse>('/api/v1/skills', params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skills');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkills(page, search);
  }, [fetchSkills, page, search]);

  const featureSkill = useCallback(async (slug: string, featured: boolean) => {
    await api.post(`/api/v1/admin/skills/${slug}/feature`, { featured });
    await fetchSkills(page, search);
  }, [fetchSkills, page, search]);

  const deprecateSkill = useCallback(async (slug: string) => {
    await api.post(`/api/v1/admin/skills/${slug}/deprecate`);
    await fetchSkills(page, search);
  }, [fetchSkills, page, search]);

  const removeSkill = useCallback(async (slug: string) => {
    await api.delete(`/api/v1/admin/skills/${slug}`);
    await fetchSkills(page, search);
  }, [fetchSkills, page, search]);

  const handleSetPage = useCallback((p: number) => {
    setPage(p);
  }, []);

  const handleSetSearch = useCallback((q: string) => {
    setSearch(q);
    setPage(1);
  }, []);

  const skills = data?.items ?? [];
  const total = data?.total ?? 0;

  return {
    skills,
    total,
    page,
    loading,
    error,
    featureSkill,
    deprecateSkill,
    removeSkill,
    setPage: handleSetPage,
    setSearch: handleSetSearch,
  };
}
