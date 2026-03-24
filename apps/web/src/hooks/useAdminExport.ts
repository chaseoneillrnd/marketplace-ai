import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../lib/api';

export interface ExportRequest {
  scope: string;
  format: string;
  start_date?: string;
  end_date?: string;
}

export interface ExportStatus {
  id: string;
  status: 'pending' | 'processing' | 'complete' | 'failed';
  download_url?: string;
}

export function useAdminExport() {
  const [exportStatus, setExportStatus] = useState<ExportStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [remainingExports, setRemainingExports] = useState(5);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const requestExport = useCallback(async (req: ExportRequest) => {
    setLoading(true);
    stopPolling();
    try {
      const result = await api.post<ExportStatus>('/api/v1/admin/exports', req);
      setExportStatus(result);
      setRemainingExports((prev) => Math.max(0, prev - 1));

      if (result.status !== 'complete' && result.status !== 'failed') {
        pollRef.current = setInterval(async () => {
          try {
            const poll = await api.get<ExportStatus>(`/api/v1/admin/exports/${result.id}`);
            setExportStatus(poll);
            if (poll.status === 'complete' || poll.status === 'failed') {
              stopPolling();
            }
          } catch {
            stopPolling();
          }
        }, 2000);
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [stopPolling]);

  return { exportStatus, loading, remainingExports, requestExport };
}
