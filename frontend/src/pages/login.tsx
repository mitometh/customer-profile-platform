import { useEffect } from "preact/hooks";

import { route } from "preact-router";

import { useAuth } from "@/hooks/use-auth";

import { Card, CardBody } from "@/components/ui/card";
import { LoginForm } from "@/features/auth/login-form";

export function LoginPage(): preact.JSX.Element | null {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      route("/", true);
    }
  }, [isLoading, isAuthenticated]);

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return null;
  }

  return (
    <div class="bg-gray-50 min-h-screen flex items-center justify-center px-4">
      <Card class="max-w-sm w-full">
        <CardBody>
          <div class="text-center mb-6">
            <h1 class="text-xl font-bold text-gray-950">
              <span class="text-indigo-600">&diams;</span> Customer 360
            </h1>
          </div>
          <LoginForm />
        </CardBody>
      </Card>
    </div>
  );
}
