import { describe, it, expect, vi, afterEach } from "vitest";

import { login, getMe } from "../auth";

// Mock the client module
vi.mock("../client", () => ({
  request: vi.fn(),
  ApiError: class extends Error {
    constructor(
      public status: number,
      public error: { code: string; message: string },
    ) {
      super(error.message);
    }
  },
}));

import { request } from "../client";

const mockRequest = vi.mocked(request);

describe("login", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("sends POST to /api/auth/login with credentials", async () => {
    const mockResponse = {
      access_token: "jwt-token",
      user: { id: "1", email: "test@test.com", full_name: "Test", role: "admin", permissions: [] },
    };
    mockRequest.mockResolvedValue(mockResponse);

    const result = await login({ email: "test@test.com", password: "pass123" });

    expect(mockRequest).toHaveBeenCalledWith("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: "test@test.com", password: "pass123" }),
    });
    expect(result).toEqual(mockResponse);
  });
});

describe("getMe", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("sends GET to /api/auth/me", async () => {
    const mockUser = { id: "1", email: "me@test.com", full_name: "Me", role: "admin", permissions: [] };
    mockRequest.mockResolvedValue(mockUser);

    const result = await getMe();

    expect(mockRequest).toHaveBeenCalledWith("/api/auth/me");
    expect(result).toEqual(mockUser);
  });
});
