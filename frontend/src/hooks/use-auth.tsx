import { createContext } from "preact";
import { useState, useEffect, useCallback, useContext } from "preact/hooks";
import type { ComponentChildren } from "preact";

import type { CurrentUser } from "@/types";

import { login as apiLogin, getMe } from "@/api/auth";
import { getToken, setToken, removeToken } from "@/lib/storage";

interface AuthContextValue {
  user: CurrentUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (code: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ComponentChildren }): ComponentChildren {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [token, setTokenState] = useState<string | null>(getToken());
  const [isLoading, setIsLoading] = useState(!!getToken());

  useEffect(() => {
    if (token) {
      getMe()
        .then(setUser)
        .catch(() => {
          removeToken();
          setTokenState(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiLogin({ email, password });
    setToken(response.access_token);
    setTokenState(response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    removeToken();
    setTokenState(null);
    setUser(null);
  }, []);

  const hasPermission = useCallback(
    (code: string): boolean => user?.permissions.includes(code) ?? false,
    [user],
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
