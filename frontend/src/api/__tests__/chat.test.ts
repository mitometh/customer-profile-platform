import { describe, it, expect, vi, afterEach } from "vitest";

import { sendMessage, getSessions, getSessionDetail } from "../chat";

vi.mock("../client", () => ({
  request: vi.fn(),
}));

import { request } from "../client";

const mockRequest = vi.mocked(request);

describe("sendMessage", () => {
  afterEach(() => vi.clearAllMocks());

  it("sends POST /api/chat with message only (new session)", async () => {
    const response = { session_id: "s1", message: { content: "Hi" }, sources: [], tool_calls: [] };
    mockRequest.mockResolvedValue(response);

    await sendMessage("Hello");

    expect(mockRequest).toHaveBeenCalledWith("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: "Hello" }),
    });
  });

  it("includes session_id when continuing a session", async () => {
    mockRequest.mockResolvedValue({});

    await sendMessage("Follow up", "sess-123");

    expect(mockRequest).toHaveBeenCalledWith("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: "Follow up", session_id: "sess-123" }),
    });
  });
});

describe("getSessions", () => {
  afterEach(() => vi.clearAllMocks());

  it("calls GET /api/chat/sessions", async () => {
    mockRequest.mockResolvedValue([]);
    await getSessions();
    expect(mockRequest).toHaveBeenCalledWith("/api/chat/sessions");
  });
});

describe("getSessionDetail", () => {
  afterEach(() => vi.clearAllMocks());

  it("calls GET /api/chat/sessions/:id", async () => {
    mockRequest.mockResolvedValue({ id: "s1", messages: [] });
    await getSessionDetail("s1");
    expect(mockRequest).toHaveBeenCalledWith("/api/chat/sessions/s1");
  });
});
