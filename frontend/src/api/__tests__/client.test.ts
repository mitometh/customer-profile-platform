import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { ApiError, request } from "../client";

describe("ApiError", () => {
  it("creates an error with status and error body", () => {
    const err = new ApiError(404, { code: "NOT_FOUND", message: "Not found" });
    expect(err.status).toBe(404);
    expect(err.error.code).toBe("NOT_FOUND");
    expect(err.error.message).toBe("Not found");
    expect(err.name).toBe("ApiError");
    expect(err.message).toBe("Not found");
  });

  it("is an instance of Error", () => {
    const err = new ApiError(500, { code: "ERROR", message: "fail" });
    expect(err).toBeInstanceOf(Error);
  });
});

describe("request", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("makes a GET request with correct headers", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1, name: "Test" }),
    });

    const result = await request<{ id: number; name: string }>("/api/v1/test");

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/test",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
    expect(result).toEqual({ id: 1, name: "Test" });
  });

  it("includes Authorization header when token exists", async () => {
    localStorage.setItem("access_token", "my-jwt-token");

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });

    await request("/api/v1/test");

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer my-jwt-token",
        }),
      }),
    );
  });

  it("throws ApiError on non-ok response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: () =>
        Promise.resolve({
          error: { code: "FORBIDDEN", message: "Access denied" },
        }),
    });

    await expect(request("/api/v1/protected")).rejects.toThrow(ApiError);

    try {
      await request("/api/v1/protected");
    } catch (e) {
      const err = e as ApiError;
      expect(err.status).toBe(403);
      expect(err.error.code).toBe("FORBIDDEN");
    }
  });

  it("returns undefined for 204 No Content", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    });

    const result = await request("/api/v1/delete-something");
    expect(result).toBeUndefined();
  });

  it("handles JSON parse failure on error response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.reject(new SyntaxError("Bad JSON")),
    });

    await expect(request("/api/v1/broken")).rejects.toThrow(ApiError);
  });
});
