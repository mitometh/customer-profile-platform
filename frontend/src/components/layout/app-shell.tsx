import { type ComponentChildren } from "preact";
import { useState } from "preact/hooks";

import { useAuth } from "@/hooks/use-auth";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

interface AppShellProps {
  children: ComponentChildren;
  currentPath?: string;
}

export function AppShell({ children, currentPath = "/" }: AppShellProps): preact.JSX.Element | null {
  const { isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div class="flex h-screen overflow-hidden bg-gray-50">
      {mobileMenuOpen && (
        <div class="fixed inset-0 z-40 md:hidden">
          <div
            class="fixed inset-0 bg-gray-950/50"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div class="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200">
            <Sidebar currentPath={currentPath} />
          </div>
        </div>
      )}

      <Sidebar currentPath={currentPath} />

      <div class="flex-1 flex flex-col min-h-screen">
        <Header onMenuToggle={() => setMobileMenuOpen((prev) => !prev)} />
        <main class="flex-1 overflow-auto">
          <div class="max-w-7xl mx-auto px-6 py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
