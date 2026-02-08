import { AuthGuard } from "@/components/layout/auth-guard";
import { PageHeader } from "@/components/layout/page-header";

import { MetricsCatalog } from "@/features/metrics/metrics-catalog";

export function MetricsCatalogPage(): preact.JSX.Element {
  return (
    <AuthGuard permission="metrics.catalog.read">
      <PageHeader title="Metrics Catalog" />
      <MetricsCatalog />
    </AuthGuard>
  );
}
