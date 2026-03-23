import { useState, useEffect, useCallback } from 'react';
import type { ReviewListResponse } from '@skillhub/shared-types';
import { api } from '../lib/api';

export function useReviews(slug: string, page = 1, perPage = 20) {
  const [data, setData] = useState<ReviewListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReviews = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<ReviewListResponse>(
        `/api/v1/skills/${slug}/reviews`,
        { page, per_page: perPage },
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reviews');
    } finally {
      setLoading(false);
    }
  }, [slug, page, perPage]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  return { data, loading, error, refetch: fetchReviews };
}
