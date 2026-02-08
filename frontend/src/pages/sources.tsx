import { AuthGuard } from "@/components/layout/auth-guard";
import { PageHeader } from "@/components/layout/page-header";

import { SourceList } from "@/features/admin/source-list";

export function SourcesPage(): preact.JSX.Element {
  return (
    <AuthGuard permission="sources.read">
      <PageHeader title="Data Sources" />
      <SourceList />
    </AuthGuard>
  );
}
