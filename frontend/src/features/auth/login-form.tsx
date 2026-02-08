import { useState } from "preact/hooks";

import { route } from "preact-router";

import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/api/client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function LoginForm(): preact.JSX.Element {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: Event): Promise<void> => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      route("/", true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.error.message);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} class="space-y-4">
      <Input
        label="Email"
        type="email"
        placeholder="you@company.com"
        value={email}
        onInput={(e) => setEmail((e.target as HTMLInputElement).value)}
        required
      />
      <Input
        label="Password"
        type="password"
        placeholder="••••••••"
        value={password}
        onInput={(e) => setPassword((e.target as HTMLInputElement).value)}
        required
      />
      {error && (
        <p class="text-sm text-red-600">{error}</p>
      )}
      <Button
        type="submit"
        variant="primary"
        loading={isLoading}
        class="w-full"
      >
        Sign in
      </Button>
    </form>
  );
}
