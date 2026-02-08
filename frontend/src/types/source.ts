export interface SourceSummary {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SourceDetail {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SourceCreateRequest {
  name: string;
  description?: string;
}

export interface SourceUpdateRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface SourceCreateResponse {
  id: string;
  name: string;
  api_token: string;
  is_active: boolean;
  created_at: string;
}
