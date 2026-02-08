import type { ChatRequest, ChatResponse } from "@/types";

import { request } from "./client";

export async function sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
  const body: ChatRequest = { message };
  if (sessionId) body.session_id = sessionId;
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
