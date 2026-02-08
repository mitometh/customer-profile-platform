import { type ComponentChildren } from "preact";
import { useEffect } from "preact/hooks";

import { route } from "preact-router";

import { useAuth } from "@/hooks/use-auth";

import { Spinner } from "@/components/ui/spinner";

interface AuthGuardProps {
  children: ComponentChildren;
  permission?: string;
}

export function AuthGuard({ children, permission }: AuthGuardProps): preact.JSX.Element | null {
  const { isAuthenticated, isLoading, hasPermission } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      route("/login", true);
    }
  }, [isLoading, isAuthenticated]);

  if (isLoading) {
    return (
      <div class="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (permission && !hasPermission(permission)) {
    return (
      <div class="flex items-center justify-center min-h-screen">
        <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-8 max-w-sm w-full text-center">
          <svg
            class="mx-auto h-12 w-12 text-gray-300"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
            />
          </svg>
          <h2 class="mt-4 text-sm font-medium text-gray-900">Access Denied</h2>
          <p class="mt-1 text-sm text-gray-500">
            You don't have permission to access this page.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
