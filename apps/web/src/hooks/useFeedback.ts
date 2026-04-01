import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface PublicFeedbackItem {
  id: string;
  category: string;
  body: string;
  upvotes: number;
  status: string;
  created_at: string | null;
}

export interface PublicFeedbackResponse {
  items: PublicFeedbackItem[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export function useFeedback() {
  const [items, setItems] = useState<PublicFeedbackItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page, per_page: 20 };
      if (category) params.category = category;
      const result = await api.get<PublicFeedbackResponse>('/api/v1/feedback', params);
      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feedback');
    } finally {
      setLoading(false);
    }
  }, [page, category]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const submitFeedback = useCallback(
    async (cat: string, body: string, skillId?: string) => {
      await api.post('/api/v1/feedback', {
        category: cat,
        body,
        ...(skillId ? { skill_id: skillId } : {}),
      });
      await fetchData();
    },
    [fetchData],
  );

  const upvote = useCallback(
    async (id: string) => {
      await api.post(`/api/v1/feedback/${id}/upvote`);
      // Optimistically update the upvote count in local state
      setItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, upvotes: item.upvotes + 1 } : item,
        ),
      );
    },
    [],
  );

  return {
    items,
    total,
    page,
    loading,
    error,
    submitFeedback,
    upvote,
    setPage,
    setCategory,
  };
}
