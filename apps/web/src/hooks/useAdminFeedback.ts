import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface FeedbackItem {
  id: string;
  category: string;
  sentiment: string;
  body: string;
  upvotes: number;
  status: string;
  skill_name: string | null;
  created_at: string;
  user_display_name: string;
}

export interface FeedbackResponse {
  items: FeedbackItem[];
  total: number;
  page: number;
  per_page: number;
}

export function useAdminFeedback(params: { category?: string; sentiment?: string; page?: number }) {
  const [data, setData] = useState<FeedbackResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const qp: Record<string, string | number> = {};
      if (params.category) qp.category = params.category;
      if (params.sentiment) qp.sentiment = params.sentiment;
      if (params.page) qp.page = params.page;
      const result = await api.get<FeedbackResponse>('/api/v1/admin/feedback', qp);
      setData(result);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [params.category, params.sentiment, params.page]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const archive = useCallback(async (id: string) => {
    await api.patch(`/api/v1/admin/feedback/${id}/status`, { status: 'archived' });
    await fetchData();
  }, [fetchData]);

  return { data, loading, refetch: fetchData, archive };
}
