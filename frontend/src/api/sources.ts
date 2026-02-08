import type { PaginatedResponse, SourceSummary, SourceDetail, SourceCreateRequest, SourceUpdateRequest, SourceCreateResponse } from "@/types";

import { DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { request } from "./client";

export async function listSources(params?: {
  cursor?: string;
  limit?: number;
}): Promise<PaginatedResponse<SourceSummary>> {
  const query = new URLSearchParams();
  if (params?.cursor) query.set("cursor", params.cursor);
  query.set("limit", String(params?.limit ?? DEFAULT_PAGE_SIZE));
  return request<PaginatedResponse<SourceSummary>>(`/api/sources?${query}`);
}

export async function getSource(id: string): Promise<SourceDetail> {
  return request<SourceDetail>(`/api/sources/${id}`);
}

export async function createSource(data: SourceCreateRequest): Promise<SourceCreateResponse> {
  return request<SourceCreateResponse>("/api/sources", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSource(id: string, data: SourceUpdateRequest): Promise<SourceDetail> {
  return request<SourceDetail>(`/api/sources/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteSource(id: string): Promise<void> {
  return request<void>(`/api/sources/${id}`, { method: "DELETE" });
}
