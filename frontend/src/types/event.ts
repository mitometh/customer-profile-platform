export type EventType = "support_ticket" | "meeting" | "usage_event";

export interface EventSummary {
  id: string;
  customer_id: string;
  event_type: EventType;
  title: string;
  description: string | null;
  occurred_at: string;
  source_name: string | null;
  data: Record<string, unknown> | null;
}

export interface EventFilters {
  event_type?: EventType;
  since?: string;
  until?: string;
  order?: "asc" | "desc";
  cursor?: string;
  limit?: number;
}
