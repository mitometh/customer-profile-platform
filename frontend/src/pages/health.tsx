import { AuthGuard } from "@/components/layout/auth-guard";
import { PageHeader } from "@/components/layout/page-header";

import { HealthDashboard } from "@/features/system/health-dashboard";

export function HealthPage(): preact.JSX.Element {
  return (
    <AuthGuard permission="system.health.read">
      <PageHeader title="System Health" />
      <HealthDashboard />
    </AuthGuard>
  );
}
