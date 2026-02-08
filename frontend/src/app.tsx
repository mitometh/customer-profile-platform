import { Component, type ComponentChildren } from "preact";
import { useEffect } from "preact/hooks";

import Router, { Route, route as navigate } from "preact-router";

import { AuthProvider, useAuth } from "@/hooks/use-auth";
import { ToastProvider } from "@/components/ui/toast";

import { AppShell } from "@/components/layout/app-shell";

import { LoginPage } from "@/pages/login";
import { ChatPage } from "@/pages/chat";
import { CustomersPage } from "@/pages/customers";
import { CustomerDetailPage } from "@/pages/customer-detail";
import { MetricsCatalogPage } from "@/pages/metrics-catalog";
import { UsersPage } from "@/pages/users";
import { SourcesPage } from "@/pages/sources";
import { RolesPage } from "@/pages/roles";
import { HealthPage } from "@/pages/health";
import { NotFoundPage } from "@/pages/not-found";

import { Spinner } from "@/components/ui/spinner";

/* ------------------------------------------------------------------ */
/*  Error Boundary                                                     */
/* ------------------------------------------------------------------ */

interface ErrorBoundaryState {
  hasError: boolean;
}

class ErrorBoundary extends Component<{ children: ComponentChildren }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  render(): ComponentChildren {
    if (this.state.hasError) {
      return (
        <div class="flex items-center justify-center min-h-screen bg-gray-50">
          <div class="text-center">
            <h1 class="text-lg font-semibold text-gray-900">Something went wrong</h1>
            <p class="text-sm text-gray-500 mt-2">
              Please refresh the page to try again.
            </p>
            <button
              type="button"
              onClick={() => globalThis.location.reload()}
              class="mt-4 inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 h-9 text-sm font-medium text-white hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Refresh
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

/* ------------------------------------------------------------------ */
/*  Loading Screen                                                     */
/* ------------------------------------------------------------------ */

function LoadingScreen(): preact.JSX.Element {
  return (
    <div class="flex items-center justify-center min-h-screen bg-gray-50" aria-live="polite">
      <div class="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p class="text-sm text-gray-500">Loading...</p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Authenticated Route Wrapper                                        */
/* ------------------------------------------------------------------ */

// Route-level component type: accepts props passed by preact-router (route params, url, etc.)
type RouteComponent = (props: Record<string, unknown>) => preact.JSX.Element | null;

interface AuthenticatedRouteProps {
  component: RouteComponent;
  path?: string;
  url?: string;
  [key: string]: unknown;
}

function AuthenticatedRoute({ component: Page, path: _path, url, ...rest }: AuthenticatedRouteProps): preact.JSX.Element | null {
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login", true);
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <AppShell currentPath={url ?? "/"}>
      <Page {...rest} />
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/*  App Router                                                         */
/* ------------------------------------------------------------------ */

function AppRouter(): preact.JSX.Element {
  const { isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Router>
      <Route path="/login" component={LoginPage} />
      <AuthenticatedRoute path="/" component={ChatPage} />
      <AuthenticatedRoute path="/customers" component={CustomersPage} />
      <AuthenticatedRoute path="/customers/:id" component={CustomerDetailPage} />
      <AuthenticatedRoute path="/metrics" component={MetricsCatalogPage} />
      <AuthenticatedRoute path="/admin/users" component={UsersPage} />
      <AuthenticatedRoute path="/admin/sources" component={SourcesPage} />
      <AuthenticatedRoute path="/admin/roles" component={RolesPage} />
      <AuthenticatedRoute path="/system/health" component={HealthPage} />
      <Route default component={NotFoundPage} />
    </Router>
  );
}

/* ------------------------------------------------------------------ */
/*  App (Root)                                                         */
/* ------------------------------------------------------------------ */

export function App(): preact.JSX.Element {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <AppRouter />
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
