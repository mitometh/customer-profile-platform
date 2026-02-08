import { request } from "./client";

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  checks: Record<string, string>;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}
