import { AuthGuard } from "@/components/layout/auth-guard";
import { PageHeader } from "@/components/layout/page-header";

import { RoleList } from "@/features/admin/role-list";

export function RolesPage(): preact.JSX.Element {
  return (
    <AuthGuard permission="roles.read">
      <PageHeader title="Roles & Permissions" />
      <RoleList />
    </AuthGuard>
  );
}
