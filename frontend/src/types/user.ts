export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface UserCreateRequest {
  email: string;
  full_name: string;
  password: string;
  role_id: string;
}

export interface UserUpdateRequest {
  full_name?: string;
  email?: string;
  role_id?: string;
  is_active?: boolean;
}
