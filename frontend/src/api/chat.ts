import type { ChatRequest, ChatResponse, SessionSummary, SessionDetail } from "@/types";

import { request } from "./client";

export async function sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
  const body: ChatRequest = { message };
  if (sessionId) body.session_id = sessionId;
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getSessions(): Promise<SessionSummary[]> {
  return request<SessionSummary[]>("/api/chat/sessions");
}

export async function getSessionDetail(sessionId: string): Promise<SessionDetail> {
  return request<SessionDetail>(`/api/chat/sessions/${sessionId}`);
}
