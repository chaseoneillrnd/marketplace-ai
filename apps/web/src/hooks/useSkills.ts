import { useState, useEffect, useCallback, useRef } from 'react';
import type { SkillBrowseResponse, SkillDetail, SortOption } from '@skillhub/shared-types';
import { CATEGORY_SLUG_MAP, DIVISION_SLUG_MAP } from '@skillhub/shared-types';
import { api } from '../lib/api';

interface BrowseParams {
  q?: string;
  category?: string;
  divisions?: string[];
  sort?: SortOption;
  install_method?: string;
  verified?: boolean;
  featured?: boolean;
  favorited?: boolean;
  page?: number;
  per_page?: number;
}

export function useSkillBrowse(params: BrowseParams) {
  const [data, setData] = useState<SkillBrowseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const paramsRef = useRef(params);
  const prevPageRef = useRef(params.page);
  paramsRef.current = params;

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const p = paramsRef.current;
      const queryParams: Record<string, string | string[] | number | boolean | undefined> = {};
      if (p.q) queryParams.q = p.q;
      if (p.category && p.category !== 'All') queryParams.category = CATEGORY_SLUG_MAP[p.category] ?? p.category;
      if (p.divisions && p.divisions.length > 0) queryParams.divisions = p.divisions.map(d => DIVISION_SLUG_MAP[d] ?? d);
      if (p.sort) queryParams.sort = p.sort;
      if (p.install_method && p.install_method !== 'All') queryParams.install_method = p.install_method;
      if (p.verified !== undefined) queryParams.verified = p.verified;
      if (p.featured !== undefined) queryParams.featured = p.featured;
      if (p.favorited !== undefined) queryParams.favorited = p.favorited;
      if (p.page) queryParams.page = p.page;
      if (p.per_page) queryParams.per_page = p.per_page;

      const result = await api.get<SkillBrowseResponse>('/api/v1/skills', queryParams);

      const isLoadMore = (p.page ?? 1) > 1 && prevPageRef.current !== p.page;
      if (isLoadMore) {
        setData(prev => prev ? {
          ...result,
          items: [...prev.items, ...result.items],
        } : result);
      } else {
        setData(result);
      }
      prevPageRef.current = p.page;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skills');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkills();
  }, [
    fetchSkills,
    params.q,
    params.category,
    params.divisions?.join(','),
    params.sort,
    params.install_method,
    params.verified,
    params.featured,
    params.favorited,
    params.page,
    params.per_page,
  ]);

  return { data, loading, error, refetch: fetchSkills };
}

export function useSkillDetail(slug: string | undefined) {
  const [data, setData] = useState<SkillDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<SkillDetail>(`/api/v1/skills/${slug}`);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skill');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  return { data, loading, error, refetch: fetchDetail };
}
