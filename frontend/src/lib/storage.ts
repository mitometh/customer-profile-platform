import { STORAGE_KEY_TOKEN } from "./constants";

export function getToken(): string | null {
  return localStorage.getItem(STORAGE_KEY_TOKEN);
}

export function setToken(token: string): void {
  localStorage.setItem(STORAGE_KEY_TOKEN, token);
}

export function removeToken(): void {
  localStorage.removeItem(STORAGE_KEY_TOKEN);
}
