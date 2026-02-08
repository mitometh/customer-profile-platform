import { AuthGuard } from "@/components/layout/auth-guard";
import { PageHeader } from "@/components/layout/page-header";

import { UserList } from "@/features/admin/user-list";

export function UsersPage(): preact.JSX.Element {
  return (
    <AuthGuard permission="users.read">
      <PageHeader title="User Management" />
      <UserList />
    </AuthGuard>
  );
}
