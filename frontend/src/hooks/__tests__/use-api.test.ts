import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/preact";

import { useApi } from "../use-api";
import { ApiError } from "@/api/client";

describe("useApi", () => {
  it("starts with initial state", () => {
    const apiFn = vi.fn();
    const { result } = renderHook(() => useApi(apiFn));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("execute sets data on success", async () => {
    const apiFn = vi.fn().mockResolvedValue({ id: 1, name: "Test" });
    const { result } = renderHook(() => useApi(apiFn));

    let returnValue: unknown;
    await act(async () => {
      returnValue = await result.current.execute();
    });

    expect(result.current.data).toEqual({ id: 1, name: "Test" });
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(returnValue).toEqual({ id: 1, name: "Test" });
  });

  it("execute sets error on ApiError", async () => {
    const apiError = new ApiError(404, { code: "NOT_FOUND", message: "Not found" });
    const apiFn = vi.fn().mockRejectedValue(apiError);
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      try {
        await result.current.execute();
      } catch {
        // expected
      }
    });

    expect(result.current.error).toBe(apiError);
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("execute re-throws errors", async () => {
    const apiError = new ApiError(500, { code: "ERR", message: "fail" });
    const apiFn = vi.fn().mockRejectedValue(apiError);
    const { result } = renderHook(() => useApi(apiFn));

    await expect(
      act(async () => {
        await result.current.execute();
      }),
    ).rejects.toThrow(apiError);
  });

  it("does not set error for non-ApiError exceptions", async () => {
    const apiFn = vi.fn().mockRejectedValue(new TypeError("type error"));
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      try {
        await result.current.execute();
      } catch {
        // expected
      }
    });

    expect(result.current.error).toBeNull(); // only ApiError is captured
  });

  it("passes arguments to apiFn", async () => {
    const apiFn = vi.fn().mockResolvedValue("ok");
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      await result.current.execute("arg1", 42);
    });

    expect(apiFn).toHaveBeenCalledWith("arg1", 42);
  });

  it("clears error on subsequent successful execute", async () => {
    const apiError = new ApiError(400, { code: "BAD", message: "bad" });
    const apiFn = vi.fn()
      .mockRejectedValueOnce(apiError)
      .mockResolvedValueOnce({ id: 2 });

    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      try { await result.current.execute(); } catch { /* expected */ }
    });
    expect(result.current.error).toBe(apiError);

    await act(async () => {
      await result.current.execute();
    });
    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual({ id: 2 });
  });

  it("reset clears all state", async () => {
    const apiFn = vi.fn().mockResolvedValue({ id: 1 });
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      await result.current.execute();
    });
    expect(result.current.data).toEqual({ id: 1 });

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });
});
