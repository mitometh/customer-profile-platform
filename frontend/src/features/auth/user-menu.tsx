import { useAuth } from "@/hooks/use-auth";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function UserMenu(): preact.JSX.Element | null {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div class="flex flex-col gap-2">
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
  );
}
