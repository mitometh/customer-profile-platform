import { useState, useCallback } from "preact/hooks";

import type { PaginatedResponse } from "@/types";

interface UsePaginationResult<T> {
  data: T[];
  isLoading: boolean;
  hasNext: boolean;
  total: number | null;
  loadMore: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function usePagination<T>(
  fetchFn: (cursor: string | undefined, limit: number) => Promise<PaginatedResponse<T>>,
  limit: number = 20,
): UsePaginationResult<T> {
  const [data, setData] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasNext, setHasNext] = useState(false);
  const [total, setTotal] = useState<number | null>(null);
  const [nextCursor, setNextCursor] = useState<string | undefined>(undefined);

  const loadMore = useCallback(async () => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const response = await fetchFn(nextCursor, limit);
      setData((prev) => [...prev, ...response.data]);
      setHasNext(response.pagination.has_next);
      setTotal(response.pagination.total);
      setNextCursor(response.pagination.next_cursor ?? undefined);
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, nextCursor, limit, isLoading]);

  const refresh = useCallback(async () => {
    setData([]);
    setNextCursor(undefined);
    setIsLoading(true);
    try {
      const response = await fetchFn(undefined, limit);
      setData(response.data);
      setHasNext(response.pagination.has_next);
      setTotal(response.pagination.total);
      setNextCursor(response.pagination.next_cursor ?? undefined);
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, limit]);

  return { data, isLoading, hasNext, total, loadMore, refresh };
}
