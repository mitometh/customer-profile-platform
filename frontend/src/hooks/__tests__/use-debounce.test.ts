import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/preact";

import { useDebounce } from "../use-debounce";

describe("useDebounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("hello", 300));
    expect(result.current).toBe("hello");
  });

  it("does not update value before delay", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "hello", delay: 300 } },
    );

    rerender({ value: "world", delay: 300 });
    vi.advanceTimersByTime(100);
    expect(result.current).toBe("hello");
  });

  it("updates value after delay", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "hello", delay: 300 } },
    );

    rerender({ value: "world", delay: 300 });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current).toBe("world");
  });

  it("resets timer on rapid changes", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "a", delay: 300 } },
    );

    rerender({ value: "b", delay: 300 });
    vi.advanceTimersByTime(100);
    rerender({ value: "c", delay: 300 });
    vi.advanceTimersByTime(100);
    rerender({ value: "d", delay: 300 });

    // Only 200ms since last change, should still be initial
    vi.advanceTimersByTime(200);
    expect(result.current).toBe("a");

    // 100ms more = 300ms since last change
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(result.current).toBe("d");
  });
});
