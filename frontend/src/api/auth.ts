import type { LoginRequest, LoginResponse, CurrentUser } from "@/types";

import { request } from "./client";

export async function login(data: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getMe(): Promise<CurrentUser> {
  return request<CurrentUser>("/api/auth/me");
}
