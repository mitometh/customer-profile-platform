import { describe, it, expect } from "vitest";

import { chatReducer, getErrorMessage } from "../chat-container";
import type { ChatState, ChatAction } from "../chat-container";
import { ApiError } from "@/api/client";

const emptyState: ChatState = {
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,
  sessions: [],
  sessionsLoading: false,
};

describe("chatReducer", () => {
  it("ADD_USER_MESSAGE appends user message and clears error", () => {
    const prev: ChatState = { ...emptyState, error: "old error" };
    const action: ChatAction = { type: "ADD_USER_MESSAGE", payload: "Hello" };
    const next = chatReducer(prev, action);

    expect(next.messages).toHaveLength(1);
    expect(next.messages[0]).toEqual({ role: "user", content: "Hello" });
    expect(next.error).toBeNull();
  });

  it("ADD_ASSISTANT_MESSAGE appends assistant message", () => {
    const prev: ChatState = {
      ...emptyState,
      messages: [{ role: "user", content: "Hi" }],
    };
    const msg = { role: "assistant" as const, content: "Hello back!" };
    const next = chatReducer(prev, { type: "ADD_ASSISTANT_MESSAGE", payload: msg });

    expect(next.messages).toHaveLength(2);
    expect(next.messages[1]?.role).toBe("assistant");
    expect(next.messages[1]?.content).toBe("Hello back!");
  });

  it("SET_LOADING updates isLoading", () => {
    const next = chatReducer(emptyState, { type: "SET_LOADING", payload: true });
    expect(next.isLoading).toBe(true);

    const next2 = chatReducer(next, { type: "SET_LOADING", payload: false });
    expect(next2.isLoading).toBe(false);
  });

  it("SET_ERROR sets error message", () => {
    const next = chatReducer(emptyState, { type: "SET_ERROR", payload: "fail" });
    expect(next.error).toBe("fail");
  });

  it("SET_ERROR clears error with null", () => {
    const prev: ChatState = { ...emptyState, error: "some error" };
    const next = chatReducer(prev, { type: "SET_ERROR", payload: null });
    expect(next.error).toBeNull();
  });

  it("SET_SESSION_ID sets the session ID", () => {
    const next = chatReducer(emptyState, { type: "SET_SESSION_ID", payload: "sess-1" });
    expect(next.sessionId).toBe("sess-1");
  });

  it("NEW_SESSION resets everything except sessions list", () => {
    const prev: ChatState = {
      sessionId: "sess-1",
      messages: [{ role: "user", content: "Hi" }],
      isLoading: true,
      error: "err",
      sessions: [{ id: "s1", title: "Old", message_count: 1, last_message_at: null, created_at: "" }],
      sessionsLoading: false,
    };
    const next = chatReducer(prev, { type: "NEW_SESSION" });

    expect(next.sessionId).toBeNull();
    expect(next.messages).toHaveLength(0);
    expect(next.isLoading).toBe(false);
    expect(next.error).toBeNull();
    expect(next.sessions).toHaveLength(1); // preserved
  });

  it("SET_SESSIONS replaces session list", () => {
    const sessions = [
      { id: "s1", title: "Chat 1", message_count: 2, last_message_at: null, created_at: "" },
      { id: "s2", title: "Chat 2", message_count: 1, last_message_at: null, created_at: "" },
    ];
    const next = chatReducer(emptyState, { type: "SET_SESSIONS", payload: sessions });
    expect(next.sessions).toHaveLength(2);
    expect(next.sessions[0]?.id).toBe("s1");
  });

  it("SET_SESSIONS_LOADING updates sessionsLoading", () => {
    const next = chatReducer(emptyState, { type: "SET_SESSIONS_LOADING", payload: true });
    expect(next.sessionsLoading).toBe(true);
  });

  it("LOAD_SESSION sets sessionId and messages", () => {
    const prev: ChatState = { ...emptyState, error: "old error" };
    const messages = [
      { role: "user" as const, content: "Hi" },
      { role: "assistant" as const, content: "Hello" },
    ];
    const next = chatReducer(prev, {
      type: "LOAD_SESSION",
      payload: { sessionId: "sess-2", messages },
    });

    expect(next.sessionId).toBe("sess-2");
    expect(next.messages).toHaveLength(2);
    expect(next.error).toBeNull();
  });

  it("returns unchanged state for unknown action", () => {
    const next = chatReducer(emptyState, { type: "UNKNOWN" } as unknown as ChatAction);
    expect(next).toBe(emptyState);
  });
});

describe("getErrorMessage", () => {
  it("maps UNAUTHORIZED error code", () => {
    const err = new ApiError(401, { code: "UNAUTHORIZED", message: "Unauthorized" });
    expect(getErrorMessage(err)).toBe("Your session has expired. Please log in again.");
  });

  it("maps FORBIDDEN error code", () => {
    const err = new ApiError(403, { code: "FORBIDDEN", message: "Forbidden" });
    expect(getErrorMessage(err)).toBe("You don't have permission to use the chat.");
  });

  it("maps RATE_LIMITED error code", () => {
    const err = new ApiError(429, { code: "RATE_LIMITED", message: "Rate limited" });
    expect(getErrorMessage(err)).toBe("Too many requests. Please wait a moment.");
  });

  it("maps LLM_UNAVAILABLE error code", () => {
    const err = new ApiError(503, { code: "LLM_UNAVAILABLE", message: "LLM down" });
    expect(getErrorMessage(err)).toBe("The AI assistant is temporarily unavailable. Please try again.");
  });

  it("maps INTERNAL_ERROR error code", () => {
    const err = new ApiError(500, { code: "INTERNAL_ERROR", message: "Internal error" });
    expect(getErrorMessage(err)).toBe("Something went wrong. Please try again.");
  });

  it("falls back to ApiError message for unknown codes", () => {
    const err = new ApiError(400, { code: "CUSTOM", message: "Custom error msg" });
    expect(getErrorMessage(err)).toBe("Custom error msg");
  });

  it("handles standard Error objects", () => {
    const err = new Error("Network failure");
    expect(getErrorMessage(err)).toBe("Network failure");
  });

  it("handles unknown error types", () => {
    expect(getErrorMessage("string error")).toBe("Something went wrong. Please try again.");
    expect(getErrorMessage(42)).toBe("Something went wrong. Please try again.");
    expect(getErrorMessage(null)).toBe("Something went wrong. Please try again.");
  });
});
