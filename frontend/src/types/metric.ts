export type MetricValueType = "integer" | "decimal" | "percentage";

export interface MetricCatalogEntry {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  unit: string | null;
  value_type: MetricValueType;
}

export interface MetricCreateRequest {
  name: string;
  display_name: string;
  description?: string;
  unit?: string;
  value_type: MetricValueType;
}

export interface MetricUpdateRequest {
  display_name?: string;
  description?: string;
  unit?: string;
  value_type?: MetricValueType;
}

export interface CustomerMetricValue {
  metric_definition_id: string;
  metric_name: string;
  display_name: string;
  metric_value: number;
  unit: string;
  description: string;
  value_type: MetricValueType;
  note: string | null;
  updated_at: string;
}

export interface MetricDataPoint {
  metric_value: number;
  recorded_at: string;
}

export interface CustomerMetricTrend {
  customer_id: string;
  metric_definition_id: string;
  metric_name: string;
  display_name: string;
  unit: string;
  data_points: MetricDataPoint[];
}
