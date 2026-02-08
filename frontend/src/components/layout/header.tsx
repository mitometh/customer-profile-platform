import { useAuth } from "@/hooks/use-auth";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Dropdown, type DropdownItem } from "@/components/ui/dropdown";

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

function LogoutIcon(): preact.JSX.Element {
  return (
    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
    </svg>
  );
}

export function Header({ onMenuToggle }: HeaderProps): preact.JSX.Element {
  const { user, logout } = useAuth();

  const dropdownItems: DropdownItem[] = [
    { label: "Logout", onClick: logout, icon: <LogoutIcon />, danger: true },
  ];

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
      {user && (
        <Dropdown trigger={
          <div class="flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2 py-1.5 transition-colors">
            <span class="text-sm font-medium text-gray-700">{user.full_name}</span>
            <Badge>{user.role}</Badge>
            <Avatar name={user.full_name} size="sm" />
          </div>
        } items={dropdownItems} />
      )}
    </header>
  );
}
