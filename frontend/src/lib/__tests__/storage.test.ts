import { describe, it, expect, beforeEach } from "vitest";

import { getToken, setToken, removeToken } from "../storage";

describe("storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when no token is set", () => {
    expect(getToken()).toBeNull();
  });

  it("stores and retrieves a token", () => {
    setToken("jwt-token-123");
    expect(getToken()).toBe("jwt-token-123");
  });

  it("removes a token", () => {
    setToken("jwt-token-123");
    removeToken();
    expect(getToken()).toBeNull();
  });

  it("overwrites existing token", () => {
    setToken("old-token");
    setToken("new-token");
    expect(getToken()).toBe("new-token");
  });
});
