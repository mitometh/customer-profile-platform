import type { PaginatedResponse, Permission, RoleSummary, RoleDetail, RoleCreateRequest, RoleUpdateRequest } from "@/types";

import { DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { request } from "./client";

export async function listRoles(params?: {
  cursor?: string;
  limit?: number;
}): Promise<PaginatedResponse<RoleSummary>> {
  const query = new URLSearchParams();
  if (params?.cursor) query.set("cursor", params.cursor);
  query.set("limit", String(params?.limit ?? DEFAULT_PAGE_SIZE));
  return request<PaginatedResponse<RoleSummary>>(`/api/roles?${query}`);
}

export async function getRoleDetail(id: string): Promise<RoleDetail> {
  return request<RoleDetail>(`/api/roles/${id}`);
}

export async function createRole(data: RoleCreateRequest): Promise<RoleDetail> {
  return request<RoleDetail>("/api/roles", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateRole(id: string, data: RoleUpdateRequest): Promise<RoleDetail> {
  return request<RoleDetail>(`/api/roles/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteRole(id: string): Promise<void> {
  return request<void>(`/api/roles/${id}`, { method: "DELETE" });
}

export async function getPermissions(): Promise<Permission[]> {
  return request<Permission[]>("/api/permissions");
}
