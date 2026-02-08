export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: CurrentUser;
}

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  permissions: string[];
}
