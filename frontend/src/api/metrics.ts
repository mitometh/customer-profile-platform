import type {
  MetricCatalogEntry,
  MetricCreateRequest,
  MetricUpdateRequest,
  CustomerMetricValue,
  CustomerMetricTrend,
} from "@/types";

import { request } from "./client";

interface MetricCatalogResponse {
  metrics: MetricCatalogEntry[];
}

interface CustomerMetricsResponse {
  customer_id: string;
  metrics: CustomerMetricValue[];
}

export async function getCatalog(): Promise<MetricCatalogResponse> {
  return request<MetricCatalogResponse>("/api/metrics/catalog");
}

export async function createMetric(data: MetricCreateRequest): Promise<MetricCatalogEntry> {
  return request<MetricCatalogEntry>("/api/metrics/catalog", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateMetric(id: string, data: MetricUpdateRequest): Promise<MetricCatalogEntry> {
  return request<MetricCatalogEntry>(`/api/metrics/catalog/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteMetric(id: string): Promise<void> {
  return request<void>(`/api/metrics/catalog/${id}`, { method: "DELETE" });
}

export async function getCustomerMetrics(customerId: string): Promise<CustomerMetricsResponse> {
  return request<CustomerMetricsResponse>(`/api/customers/${customerId}/metrics`);
}

export async function getMetricHistory(
  customerId: string,
  metricId: string,
  params?: { since?: string; until?: string; limit?: number },
): Promise<CustomerMetricTrend> {
  const query = new URLSearchParams();
  if (params?.since) query.set("since", params.since);
  if (params?.until) query.set("until", params.until);
  if (params?.limit) query.set("limit", String(params.limit));
  return request<CustomerMetricTrend>(`/api/customers/${customerId}/metrics/${metricId}/history?${query}`);
}
