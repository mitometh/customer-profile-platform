import type { PaginatedResponse, UserSummary, UserCreateRequest, UserUpdateRequest } from "@/types";

import { DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { request } from "./client";

export async function listUsers(params?: {
  cursor?: string;
  limit?: number;
}): Promise<PaginatedResponse<UserSummary>> {
  const query = new URLSearchParams();
  if (params?.cursor) query.set("cursor", params.cursor);
  query.set("limit", String(params?.limit ?? DEFAULT_PAGE_SIZE));
  return request<PaginatedResponse<UserSummary>>(`/api/users?${query}`);
}

export async function createUser(data: UserCreateRequest): Promise<UserSummary> {
  return request<UserSummary>("/api/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateUser(id: string, data: UserUpdateRequest): Promise<UserSummary> {
  return request<UserSummary>(`/api/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
