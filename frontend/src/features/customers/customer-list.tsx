import { useState, useEffect, useCallback } from "preact/hooks";

import { route } from "preact-router";

import type { CustomerSummary } from "@/types";

import { listCustomers } from "@/api/customers";
import { useDebounce } from "@/hooks/use-debounce";
import { usePagination } from "@/hooks/use-pagination";
import { usePermission } from "@/hooks/use-permission";
import { formatCurrency, formatDate } from "@/lib/format";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { DataTable, type Column } from "@/components/data/data-table";
import { PaginationControls } from "@/components/data/pagination-controls";

import { CustomerForm } from "@/features/customers/customer-form";

const columns: Column<CustomerSummary>[] = [
  {
    key: "company_name",
    header: "Company Name",
    render: (item) => (
      <span class="font-medium text-gray-900">{item.company_name}</span>
    ),
  },
  {
    key: "contact_name",
    header: "Contact",
  },
  {
    key: "email",
    header: "Email",
    class: "text-gray-500",
  },
  {
    key: "contract_value",
    header: "Contract Value",
    render: (item) => formatCurrency(item.contract_value, item.currency_code),
  },
  {
    key: "signup_date",
    header: "Signup Date",
    render: (item) => formatDate(item.signup_date),
  },
  {
    key: "source_name",
    header: "Source",
    render: (item) =>
      item.source_name ? (
        <Badge>{item.source_name}</Badge>
      ) : (
        <span class="text-gray-400">&mdash;</span>
      ),
  },
];

export function CustomerList(): preact.JSX.Element {
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const debouncedSearch = useDebounce(search);
  const { hasPermission } = usePermission();

  const fetchFn = useCallback(
    (cursor: string | undefined, limit: number) =>
      listCustomers({ search: debouncedSearch || undefined, cursor, limit }),
    [debouncedSearch],
  );

  const { data, isLoading, hasNext, total, loadMore, refresh } = usePagination<CustomerSummary>(fetchFn);

  useEffect(() => {
    refresh();
  }, [debouncedSearch]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRowClick = (customer: CustomerSummary): void => {
    route(`/customers/${customer.id}`);
  };

  const handleSearchInput = (e: Event): void => {
    setSearch((e.target as HTMLInputElement).value);
  };

  const handleFormSuccess = (): void => {
    setShowForm(false);
    refresh();
  };

  return (
    <div>
      <div class="flex items-center gap-4 mb-6">
        <div class="flex-1">
          <Input
            placeholder="Search customers..."
            value={search}
            onInput={handleSearchInput}
          />
        </div>
        {hasPermission("customers.manage") && (
          <Button onClick={() => setShowForm(true)}>
            Add Customer
          </Button>
        )}
      </div>

      <DataTable
        columns={columns as unknown as Column<Record<string, unknown>>[]}
        data={data as unknown as Record<string, unknown>[]}
        onRowClick={(item) => handleRowClick(item as unknown as CustomerSummary)}
        isLoading={isLoading && data.length === 0}
        emptyMessage="No customers found"
      />

      {data.length > 0 && (
        <PaginationControls
          hasNext={hasNext}
          isLoading={isLoading}
          total={total}
          currentCount={data.length}
          onLoadMore={loadMore}
        />
      )}

      {showForm && (
        <CustomerForm
          isOpen={showForm}
          onClose={() => setShowForm(false)}
          onSuccess={handleFormSuccess}
        />
      )}
    </div>
  );
}
