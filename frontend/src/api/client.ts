import { API_BASE_URL } from "@/lib/constants";
import { getToken } from "@/lib/storage";

export class ApiError extends Error {
  constructor(
    public status: number,
    public error: { code: string; message: string; details?: Record<string, unknown> },
  ) {
    super(error.message);
    this.name = "ApiError";
  }
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { ...headers, ...options?.headers },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({
      error: { code: "UNKNOWN", message: "An unexpected error occurred" },
    }));
    throw new ApiError(res.status, body.error);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}
