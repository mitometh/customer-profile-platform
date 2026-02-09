import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/preact";

import { usePagination } from "../use-pagination";
import type { PaginatedResponse } from "@/types";

function makePage<T>(data: T[], hasNext: boolean, cursor?: string, total?: number, limit = 20): PaginatedResponse<T> {
  return {
    data,
    pagination: {
      has_next: hasNext,
      next_cursor: cursor ?? null,
      total: total ?? data.length,
      limit,
    },
  };
}

describe("usePagination", () => {
  it("starts with empty state", () => {
    const fetchFn = vi.fn();
    const { result } = renderHook(() => usePagination(fetchFn));

    expect(result.current.data).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.hasNext).toBe(false);
    expect(result.current.total).toBeNull();
  });

  it("refresh loads first page", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      makePage([{ id: 1 }, { id: 2 }], true, "cursor-2", 10),
    );

    const { result } = renderHook(() => usePagination(fetchFn, 2));

    await act(async () => {
      await result.current.refresh();
    });

    expect(fetchFn).toHaveBeenCalledWith(undefined, 2);
    expect(result.current.data).toEqual([{ id: 1 }, { id: 2 }]);
    expect(result.current.hasNext).toBe(true);
    expect(result.current.total).toBe(10);
  });

  it("loadMore appends data", async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce(makePage([{ id: 1 }], true, "cur-1", 3))
      .mockResolvedValueOnce(makePage([{ id: 2 }], true, "cur-2", 3))
      .mockResolvedValueOnce(makePage([{ id: 3 }], false, undefined, 3));

    const { result } = renderHook(() => usePagination(fetchFn, 1));

    await act(async () => {
      await result.current.refresh();
    });
    expect(result.current.data).toHaveLength(1);

    await act(async () => {
      await result.current.loadMore();
    });
    expect(result.current.data).toHaveLength(2);
    expect(fetchFn).toHaveBeenLastCalledWith("cur-1", 1);

    await act(async () => {
      await result.current.loadMore();
    });
    expect(result.current.data).toHaveLength(3);
    expect(result.current.hasNext).toBe(false);
  });

  it("refresh resets accumulated data", async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce(makePage([{ id: 1 }], true, "cur-1", 2))
      .mockResolvedValueOnce(makePage([{ id: 2 }], false, undefined, 2))
      .mockResolvedValueOnce(makePage([{ id: 10 }], false, undefined, 1));

    const { result } = renderHook(() => usePagination(fetchFn, 1));

    await act(async () => {
      await result.current.refresh();
    });
    await act(async () => {
      await result.current.loadMore();
    });
    expect(result.current.data).toHaveLength(2);

    // Refresh should reset
    await act(async () => {
      await result.current.refresh();
    });
    expect(result.current.data).toEqual([{ id: 10 }]);
    expect(result.current.total).toBe(1);
  });

  it("handles fetch errors gracefully", async () => {
    const fetchFn = vi.fn().mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => usePagination(fetchFn));

    await act(async () => {
      try {
        await result.current.refresh();
      } catch {
        // expected
      }
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toEqual([]);
  });

  it("uses default limit of 20", async () => {
    const fetchFn = vi.fn().mockResolvedValue(makePage([], false));

    const { result } = renderHook(() => usePagination(fetchFn));

    await act(async () => {
      await result.current.refresh();
    });

    expect(fetchFn).toHaveBeenCalledWith(undefined, 20);
  });
});
