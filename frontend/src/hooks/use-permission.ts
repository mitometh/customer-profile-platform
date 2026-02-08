import { useAuth } from "./use-auth";

export function usePermission(): {
  hasPermission: (code: string) => boolean;
  canAccess: (codes: string[]) => boolean;
} {
  const { hasPermission } = useAuth();

  const canAccess = (codes: string[]): boolean =>
    codes.some((code) => hasPermission(code));

  return { hasPermission, canAccess };
}
