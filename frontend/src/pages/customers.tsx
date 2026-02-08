import { AuthGuard } from "@/components/layout/auth-guard";
import { PageHeader } from "@/components/layout/page-header";

import { CustomerList } from "@/features/customers/customer-list";

export function CustomersPage(): preact.JSX.Element {
  return (
    <AuthGuard permission="customers.read">
      <PageHeader title="Customers" />
      <CustomerList />
    </AuthGuard>
  );
}
