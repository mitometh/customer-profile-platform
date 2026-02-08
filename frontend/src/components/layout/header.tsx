import { useAuth } from "@/hooks/use-auth";

import { Badge } from "@/components/ui/badge";

interface HeaderProps {
  onMenuToggle?: () => void;
}

function MenuIcon(): preact.JSX.Element {
  return (
    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
  );
}

export function Header({ onMenuToggle }: HeaderProps): preact.JSX.Element {
  const { user } = useAuth();

  return (
    <header class="flex items-center justify-between h-14 px-6 border-b border-gray-200 bg-white">
      <div class="flex items-center">
        {onMenuToggle && (
          <button
            type="button"
            onClick={onMenuToggle}
            class="lg:hidden inline-flex items-center justify-center p-2 -ml-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            aria-label="Toggle navigation menu"
          >
            <MenuIcon />
          </button>
        )}
      </div>
      <div class="flex items-center gap-3">
        {user && (
          <>
            <span class="text-sm font-medium text-gray-700">{user.full_name}</span>
            <Badge>{user.role}</Badge>
          </>
        )}
      </div>
    </header>
  );
}
