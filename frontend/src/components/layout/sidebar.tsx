import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";
import { useAuth } from "@/hooks/use-auth";
import { usePermission } from "@/hooks/use-permission";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface SidebarProps {
  currentPath: string;
  collapsed?: boolean;
}

interface NavItem {
  label: string;
  href: string;
  permission: string;
  icon: ComponentChildren;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

function ChatIcon(): preact.JSX.Element {
  return (
    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
    </svg>
  );
}

function UsersIcon(): preact.JSX.Element {
  return (
    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
    </svg>
  );
}

function ChartBarIcon(): preact.JSX.Element {
  return (
    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function ShieldIcon(): preact.JSX.Element {
  return (
    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  );
}

function ServerIcon(): preact.JSX.Element {
  return (
    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 17.25v-.228a4.5 4.5 0 0 0-.12-1.03l-2.268-9.64a3.375 3.375 0 0 0-3.285-2.602H7.923a3.375 3.375 0 0 0-3.285 2.602l-2.268 9.64a4.5 4.5 0 0 0-.12 1.03v.228m19.5 0a3 3 0 0 1-3 3H5.25a3 3 0 0 1-3-3m19.5 0a3 3 0 0 0-3-3H5.25a3 3 0 0 0-3 3m16.5 0h.008v.008h-.008v-.008Zm-3 0h.008v.008h-.008v-.008Z" />
    </svg>
  );
}

function HeartIcon(): preact.JSX.Element {
  return (
    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
    </svg>
  );
}

const NAV_SECTIONS: NavSection[] = [
  {
    label: "Main",
    items: [
      { label: "Chat", href: "/", permission: "chat.use", icon: <ChatIcon /> },
      { label: "Customers", href: "/customers", permission: "customers.read", icon: <UsersIcon /> },
    ],
  },
  {
    label: "Analytics",
    items: [
      { label: "Metrics", href: "/metrics", permission: "metrics.catalog.read", icon: <ChartBarIcon /> },
    ],
  },
  {
    label: "Administration",
    items: [
      { label: "Users", href: "/admin/users", permission: "users.read", icon: <ShieldIcon /> },
      { label: "Sources", href: "/admin/sources", permission: "sources.read", icon: <ServerIcon /> },
      { label: "Roles", href: "/admin/roles", permission: "roles.read", icon: <ShieldIcon /> },
    ],
  },
  {
    label: "System",
    items: [
      { label: "Health", href: "/system/health", permission: "system.health.read", icon: <HeartIcon /> },
    ],
  },
];

function isActive(currentPath: string, href: string): boolean {
  if (href === "/") {
    return currentPath === "/";
  }
  return currentPath === href || currentPath.startsWith(href + "/");
}

export function Sidebar({ currentPath, collapsed }: SidebarProps): preact.JSX.Element {
  const { user, logout } = useAuth();
  const { hasPermission } = usePermission();

  return (
    <aside
      class={cn(
        "hidden md:flex flex-col bg-white border-r border-gray-200 h-screen",
        collapsed ? "w-16" : "lg:w-64 w-16",
      )}
    >
      <div class={cn("flex items-center gap-2 px-4 h-14 border-b border-gray-200", collapsed && "justify-center")}>
        <span class="text-indigo-600 font-bold text-lg">&diams;</span>
        {!collapsed && <span class="hidden lg:inline text-lg font-bold text-gray-950">Customer 360</span>}
      </div>

      <nav class="flex-1 overflow-y-auto py-4 px-2">
        {NAV_SECTIONS.map((section) => {
          const visibleItems = section.items.filter((item) =>
            hasPermission(item.permission),
          );

          if (visibleItems.length === 0) {
            return null;
          }

          return (
            <div key={section.label} class="mb-4">
              {!collapsed && (
                <div class="hidden lg:block text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-1">
                  {section.label}
                </div>
              )}
              {visibleItems.map((item) => {
                const active = isActive(currentPath, item.href);
                return (
                  <a
                    key={item.href}
                    href={item.href}
                    class={cn(
                      "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                      collapsed && "justify-center",
                      active
                        ? "bg-indigo-100 text-indigo-700"
                        : "text-gray-600 hover:bg-gray-100",
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    {item.icon}
                    {!collapsed && <span class="hidden lg:inline">{item.label}</span>}
                  </a>
                );
              })}
            </div>
          );
        })}
      </nav>

      {user && (
        <div class={cn("border-t border-gray-200 p-4 mt-auto", collapsed && "flex flex-col items-center p-2")}>
          {collapsed ? (
            <Avatar name={user.full_name} size="sm" />
          ) : (
            <div class="hidden lg:flex flex-col gap-2">
              <div class="flex items-center gap-3">
                <Avatar name={user.full_name} size="sm" />
                <div class="min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">{user.full_name}</p>
                  <Badge>{user.role}</Badge>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={logout} class="w-full justify-start">
                Logout
              </Button>
            </div>
          )}
          {!collapsed && (
            <div class="lg:hidden flex flex-col items-center">
              <Avatar name={user.full_name} size="sm" />
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
