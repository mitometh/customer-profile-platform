import type { CustomerSummary } from "@/types";

import { cn } from "@/lib/cn";
import { formatCurrency, formatDate } from "@/lib/format";

import { Badge } from "@/components/ui/badge";
import { Card, CardBody } from "@/components/ui/card";

interface CustomerCardProps {
  customer: CustomerSummary;
  onClick?: () => void;
}

export function CustomerCard({ customer, onClick }: CustomerCardProps): preact.JSX.Element {
  return (
    <Card
      class={cn(onClick && "cursor-pointer hover:border-indigo-200 transition-colors")}
    >
      <CardBody>
        <div onClick={onClick}>
          <h3 class="text-base font-semibold text-gray-950 truncate">
            {customer.company_name}
          </h3>
          <p class="text-sm text-gray-700 mt-1">{customer.contact_name}</p>
          <p class="text-sm text-gray-500 truncate">{customer.email}</p>
          <div class="flex items-center gap-2 mt-3">
            <span class="text-sm font-medium text-gray-900">
              {formatCurrency(customer.contract_value, customer.currency_code)}
            </span>
            <Badge>{customer.currency_code}</Badge>
          </div>
          <div class="flex items-center justify-between mt-3">
            <span class="text-xs text-gray-500">
              {formatDate(customer.signup_date)}
            </span>
            {customer.source_name ? (
              <Badge variant="primary">{customer.source_name}</Badge>
            ) : (
              <span class="text-xs text-gray-400">&mdash;</span>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
