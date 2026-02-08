export interface Permission {
  id: string;
  code: string;
  description: string;
}

export interface RoleSummary {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  is_system: boolean;
  permission_count: number;
  created_at: string;
}

export interface RoleDetail {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  is_system: boolean;
  permissions: Permission[];
  user_count: number;
  created_at: string;
  updated_at: string;
}

export interface RoleCreateRequest {
  name: string;
  display_name: string;
  description?: string;
  permissions: string[];
}

export interface RoleUpdateRequest {
  display_name?: string;
  description?: string;
  permissions?: string[];
}
