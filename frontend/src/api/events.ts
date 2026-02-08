import type { PaginatedResponse, EventSummary, EventFilters } from "@/types";

import { DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { request } from "./client";

export async function getCustomerEvents(
  customerId: string,
  filters?: EventFilters,
): Promise<PaginatedResponse<EventSummary>> {
  const query = new URLSearchParams();
  if (filters?.event_type) query.set("event_type", filters.event_type);
  if (filters?.since) query.set("since", filters.since);
  if (filters?.until) query.set("until", filters.until);
  if (filters?.order) query.set("order", filters.order);
  if (filters?.cursor) query.set("cursor", filters.cursor);
  query.set("limit", String(filters?.limit ?? DEFAULT_PAGE_SIZE));
  return request<PaginatedResponse<EventSummary>>(`/api/customers/${customerId}/events?${query}`);
}
