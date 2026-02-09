import type { EventSummary } from "./event";
import type { CustomerMetricValue } from "./metric";

export interface CustomerSummary {
  id: string;
  company_name: string;
  contact_name: string;
  email: string;
  contract_value: number;
  currency_code: string;
  signup_date: string;
  source_name: string | null;
}

export interface CustomerDetail {
  id: string;
  company_name: string;
  contact_name: string;
  email: string;
  phone: string | null;
  industry: string | null;
  contract_value: number;
  currency_code: string;
  signup_date: string;
  source_name: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  recent_events: EventSummary[];
  metrics: CustomerMetricValue[];
}

export interface CustomerCreateRequest {
  company_name: string;
  contact_name: string;
  email: string;
  contract_value: number;
  currency_code: string;
  signup_date: string;
}

export interface CustomerUpdateRequest {
  company_name?: string;
  contact_name?: string;
  email?: string;
  contract_value?: number;
  currency_code?: string;
}
