import type { PaginatedResponse, CustomerSummary, CustomerDetail, CustomerCreateRequest, CustomerUpdateRequest } from "@/types";

import { DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { request } from "./client";

export async function listCustomers(params?: {
  search?: string;
  cursor?: string;
  limit?: number;
}): Promise<PaginatedResponse<CustomerSummary>> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.cursor) query.set("cursor", params.cursor);
  query.set("limit", String(params?.limit ?? DEFAULT_PAGE_SIZE));
  return request<PaginatedResponse<CustomerSummary>>(`/api/customers?${query}`);
}

export async function getCustomer(id: string): Promise<CustomerDetail> {
  return request<CustomerDetail>(`/api/customers/${id}`);
}

export async function createCustomer(data: CustomerCreateRequest): Promise<CustomerDetail> {
  return request<CustomerDetail>("/api/customers", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCustomer(id: string, data: CustomerUpdateRequest): Promise<CustomerDetail> {
  return request<CustomerDetail>(`/api/customers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteCustomer(id: string): Promise<void> {
  return request<void>(`/api/customers/${id}`, { method: "DELETE" });
}
